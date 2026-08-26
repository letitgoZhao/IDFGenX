from pathlib import Path
import unittest

from idfgenx.data_factory.scenarios import load_scenario_catalog, scenario_catalog_sha256, validate_bucket_assignment
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class ScenarioCatalogTests(unittest.TestCase):
    def test_catalog_freezes_ten_buckets_and_c5_is_evaluation_only(self) -> None:
        catalog = load_scenario_catalog(Path("configs/data/scenario_buckets_v0_1.json"))
        self.assertEqual(len(catalog.buckets), 10)
        self.assertEqual(catalog.evaluation_only_bucket_ids, ("C5",))
        self.assertFalse(catalog.bucket("C5").training_eligible)

    def test_rejects_c5_for_training_and_small_perimeter_core(self) -> None:
        catalog = load_scenario_catalog(Path("configs/data/scenario_buckets_v0_1.json"))
        c5 = ResolvedScenarioSpec(building_name="OOD", length_m=4, width_m=20, floor_to_floor_height_m=3, stories=1, zone_layout=ZoneLayout.SINGLE, perimeter_depth_m=None, window_to_wall_ratio=.2, heating_setpoint_c=18, cooling_setpoint_c=24, building_use=BuildingUse.OFFICE)
        with self.assertRaises(ValueError):
            validate_bucket_assignment(c5, catalog.bucket("C5"), for_training=True)
        small_core = ResolvedScenarioSpec(building_name="Core", length_m=10, width_m=14, floor_to_floor_height_m=3, stories=2, zone_layout=ZoneLayout.PERIMETER_CORE, perimeter_depth_m=2.5, window_to_wall_ratio=.3, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
        with self.assertRaises(ValueError):
            validate_bucket_assignment(small_core, catalog.bucket("S2"))

    def test_catalog_hash_is_stable(self) -> None:
        catalog = load_scenario_catalog(Path("configs/data/scenario_buckets_v0_1.json"))
        self.assertEqual(scenario_catalog_sha256(catalog), scenario_catalog_sha256(catalog))
