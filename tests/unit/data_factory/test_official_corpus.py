"""EnergyPlus 官方语料解析、筛选策略和去重逻辑测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from idfgenx.data_factory.official_corpus import (
    _copy_target_for,
    build_source_record,
    classify_complexity,
    parse_idf_objects,
    select_records,
    strip_idf_comments,
)


SIMPLE_IDF = """
Version, 23.1;
Building, Demo;
Zone, Zone 1;
BuildingSurface:Detailed,
  Wall 1, Wall, Construction, Zone 1, , Outdoors, , SunExposed,
  WindExposed, , 4, 0,0,0, 10,0,0, 10,0,3, 0,0,3;
"""


class OfficialCorpusParsingTests(unittest.TestCase):
    """验证轻量 IDF 解析过程不会破坏建档所需的不变量。"""

    def test_comments_are_removed_without_dropping_objects(self) -> None:
        text = "Version, 23.1; ! comment\nZone, Main Zone;"

        stripped = strip_idf_comments(text)
        objects = parse_idf_objects(text)

        self.assertNotIn("comment", stripped)
        self.assertEqual([obj.object_type for obj in objects], ["version", "zone"])

    def test_simple_geometry_rule_is_explicit(self) -> None:
        complexity, reasons = classify_complexity(
            zone_count=1,
            surface_count=6,
            fenestration_count=4,
            shading_count=0,
            interzone_surface_count=0,
            nonquad_surface_count=0,
        )

        self.assertEqual(complexity, "simple")
        self.assertEqual(reasons, [])

    def test_multi_zone_geometry_is_complex(self) -> None:
        complexity, reasons = classify_complexity(
            zone_count=2,
            surface_count=12,
            fenestration_count=2,
            shading_count=0,
            interzone_surface_count=2,
            nonquad_surface_count=0,
        )

        self.assertEqual(complexity, "complex")
        self.assertIn("multi_zone", reasons)
        self.assertIn("has_interzone_surfaces", reasons)


class OfficialCorpusPolicyTests(unittest.TestCase):
    """验证范围排除规则和语义去重行为。"""

    def _record(self, root: Path, relative: str, text: str):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return build_source_record(path, root, "example")

    def test_real_air_loop_is_not_training_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = self._record(
                root,
                "ExampleFiles/air_loop.idf",
                SIMPLE_IDF + "\nAirLoopHVAC, Main Air Loop;\n",
            )

        self.assertFalse(record.training_eligible)
        self.assertIn("unsupported_hvac", record.rejection_reasons)
        self.assertIn("airloophvac", record.unsupported_hvac_types)

    def test_schedule_file_is_an_external_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = self._record(
                root,
                "ExampleFiles/external.idf",
                SIMPLE_IDF + "\nSchedule:File, External Schedule, Any Number, file.csv;\n",
            )

        self.assertFalse(record.training_eligible)
        self.assertEqual(record.external_dependency_types, ["schedule:file"])

    def test_shading_and_window_data_files_are_external_dependencies(self) -> None:
        for object_text, expected_type in (
            ("Schedule:File:Shading, shading.csv;", "schedule:file:shading"),
            (
                "Construction:WindowDataFile, Window, window.dat;",
                "construction:windowdatafile",
            ),
        ):
            with self.subTest(object_type=expected_type):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    record = self._record(
                        root,
                        "ExampleFiles/external_data.idf",
                        SIMPLE_IDF + "\n" + object_text + "\n",
                    )

                self.assertFalse(record.training_eligible)
                self.assertIn(expected_type, record.external_dependency_types)

    def test_specialized_zone_equipment_is_outside_hvac_scope(self) -> None:
        for object_text, expected_type in (
            ("ZoneEarthtube, Earth Tube;", "zoneearthtube"),
            ("ZoneCoolTower:Shower, Cool Tower;", "zonecooltower:shower"),
            ("ZoneThermalChimney, Chimney;", "zonethermalchimney"),
        ):
            with self.subTest(object_type=expected_type):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    record = self._record(
                        root,
                        "ExampleFiles/zone_equipment.idf",
                        SIMPLE_IDF + "\n" + object_text + "\n",
                    )

                self.assertFalse(record.training_eligible)
                self.assertIn(expected_type, record.unsupported_hvac_types)

    def test_advanced_ground_domain_is_outside_feature_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = self._record(
                root,
                "ExampleFiles/ground_domain.idf",
                SIMPLE_IDF + "\nSite:GroundDomain:Slab, Ground Domain;\n",
            )

        self.assertFalse(record.training_eligible)
        self.assertIn("site:grounddomain:slab", record.unsupported_feature_types)

    def test_scientific_notation_like_name_is_not_treated_as_vertex_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = self._record(
                root,
                "ExampleFiles/scientific_name.idf",
                SIMPLE_IDF.replace("Wall 1", "8E9267"),
            )

        self.assertEqual(record.surface_count, 1)
        self.assertEqual(record.nonquad_surface_count, 0)

    def test_output_only_variants_share_semantic_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self._record(
                root,
                "ExampleFiles/first.idf",
                SIMPLE_IDF + "\nOutput:Variable, *, Zone Mean Air Temperature, Hourly;\n",
            )
            second = self._record(
                root,
                "ExampleFiles/second.idf",
                SIMPLE_IDF + "\nOutput:Variable, *, Zone Mean Air Temperature, Timestep;\n",
            )

        self.assertEqual(first.semantic_sha256, second.semantic_sha256)
        self.assertNotEqual(first.normalized_sha256, second.normalized_sha256)

    def test_semantic_duplicates_select_one_representative(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self._record(root, "ExampleFiles/a.idf", SIMPLE_IDF)
            second = self._record(root, "ExampleFiles/nested/b.idf", SIMPLE_IDF)
            records = [second, first]

            select_records(
                records,
                simple_seed_paths={"ExampleFiles/a.idf"},
                complex_seed_paths=set(),
                geometry_reference_paths=set(),
            )

        self.assertEqual(first.selected_role, "seed_simple")
        self.assertEqual(second.duplicate_of, first.source_relative_path)
        self.assertIn("semantic_duplicate", second.rejection_reasons)

    def test_selected_idfs_are_grouped_under_one_idf_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record = self._record(root, "ExampleFiles/seed.idf", SIMPLE_IDF)

        expected_paths = {
            "seed_simple": Path("idf/simple/seed.idf"),
            "seed_complex": Path("idf/complex/seed.idf"),
            "reference_geometry": Path("idf/geometry_references/seed.idf"),
            "template": Path("idf/templates/seed.idf"),
        }
        for selected_role, expected_path in expected_paths.items():
            with self.subTest(selected_role=selected_role):
                record.selected_role = selected_role
                self.assertEqual(_copy_target_for(record), expected_path)

    def test_distinct_seeds_with_same_geometry_are_not_marked_as_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self._record(
                root,
                "ExampleFiles/first.idf",
                SIMPLE_IDF + "\nPeople, People 1, Zone 1, Always On, People;\n",
            )
            second = self._record(
                root,
                "ExampleFiles/second.idf",
                SIMPLE_IDF + "\nLights, Lights 1, Zone 1, Always On, Watts/Area;\n",
            )

            select_records(
                [first, second],
                simple_seed_paths={
                    "ExampleFiles/first.idf",
                    "ExampleFiles/second.idf",
                },
                complex_seed_paths=set(),
                geometry_reference_paths=set(),
            )

        self.assertIsNone(first.duplicate_of)
        self.assertIsNone(second.duplicate_of)


if __name__ == "__main__":
    unittest.main()
