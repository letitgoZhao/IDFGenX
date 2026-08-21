"""官方 IDF 语料哈希与质量门禁测试。"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from idfgenx.data_factory.validate_official_corpus import (
    load_selected_manifest,
    select_seed_records,
    verify_copy_hashes,
)


class OfficialCorpusValidationTests(unittest.TestCase):
    """验证清单读取、角色过滤和副本完整性检查。"""

    def _build_corpus(self, root: Path, content: bytes = b"Version,23.1;\n") -> None:
        idf_path = root / "idf" / "simple" / "seed.idf"
        idf_path.parent.mkdir(parents=True, exist_ok=True)
        idf_path.write_bytes(content)
        metadata_path = root / "metadata"
        metadata_path.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(content).hexdigest()
        records = [
            {
                "source_relative_path": "ExampleFiles/seed.idf",
                "copied_relative_path": "idf/simple/seed.idf",
                "source_sha256": digest,
                "copied_sha256": digest,
                "selected_role": "seed_simple",
            },
            {
                "source_relative_path": "ExampleFiles/reference.idf",
                "copied_relative_path": "idf/geometry_references/reference.idf",
                "source_sha256": "unused",
                "copied_sha256": "unused",
                "selected_role": "reference_geometry",
            },
        ]
        manifest = metadata_path / "selected_manifest.jsonl"
        manifest.write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_manifest_loader_and_seed_filter_ignore_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._build_corpus(root)

            records = load_selected_manifest(root)
            seeds = select_seed_records(records)

        self.assertEqual(len(records), 2)
        self.assertEqual([record["selected_role"] for record in seeds], ["seed_simple"])

    def test_hash_verification_detects_file_changed_after_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._build_corpus(root)
            records = load_selected_manifest(root)
            initial_results = verify_copy_hashes(root, records[:1])
            (root / "idf" / "simple" / "seed.idf").write_bytes(b"changed")
            changed_results = verify_copy_hashes(root, records[:1])

        self.assertTrue(initial_results[0]["passed"])
        self.assertFalse(changed_results[0]["passed"])


if __name__ == "__main__":
    unittest.main()
