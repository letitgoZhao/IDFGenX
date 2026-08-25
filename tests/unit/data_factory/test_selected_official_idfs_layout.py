"""精选官方 IDF 规范目录和快照完整性测试。"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from idfgenx.data_factory.validate_official_corpus import (
    load_selected_manifest,
    verify_copy_hashes,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CORPUS_ROOT = REPOSITORY_ROOT / "data" / "selected_official_idfs"
OLD_CORPUS_ROOT = REPOSITORY_ROOT / "data" / "official_idf_v23_1"


class SelectedOfficialIdfsLayoutTests(unittest.TestCase):
    """验证精选快照只有一个规范位置且副本内容不变。"""

    def test_only_canonical_corpus_directory_exists(self) -> None:
        """迁移后不得保留会形成双重事实源的旧目录。"""

        self.assertTrue(CORPUS_ROOT.is_dir())
        self.assertFalse(OLD_CORPUS_ROOT.exists())

    def test_manifest_resolves_all_68_unchanged_copies(self) -> None:
        """每个精选副本必须仍能按 manifest 路径解析且哈希一致。"""

        records = load_selected_manifest(CORPUS_ROOT)
        hash_results = verify_copy_hashes(CORPUS_ROOT, records)

        self.assertEqual(len(records), 68)
        self.assertEqual(len(list(CORPUS_ROOT.glob("idf/**/*.idf"))), 68)
        self.assertTrue(all(bool(result["passed"]) for result in hash_results))

    def test_git_clean_filter_preserves_snapshot_bytes(self) -> None:
        """Git 暂存过滤器不得改变全部官方 IDF 和许可证的原始字节。"""

        records = load_selected_manifest(CORPUS_ROOT)
        relative_paths = [
            (CORPUS_ROOT / str(record["copied_relative_path"]))
            .relative_to(REPOSITORY_ROOT)
            .as_posix()
            for record in records
        ]
        relative_paths.append(
            (CORPUS_ROOT / "LICENSE.txt")
            .relative_to(REPOSITORY_ROOT)
            .as_posix()
        )

        self.assertEqual(len(relative_paths), 69)
        for relative_path in relative_paths:
            with self.subTest(relative_path=relative_path):
                filtered_hash = subprocess.check_output(
                    ["git", "hash-object", relative_path],
                    cwd=REPOSITORY_ROOT,
                    text=True,
                ).strip()
                raw_hash = subprocess.check_output(
                    ["git", "hash-object", "--no-filters", relative_path],
                    cwd=REPOSITORY_ROOT,
                    text=True,
                ).strip()
                self.assertEqual(filtered_hash, raw_hash)


if __name__ == "__main__":
    unittest.main()
