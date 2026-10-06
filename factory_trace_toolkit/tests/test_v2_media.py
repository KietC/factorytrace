"""English: Ensure exact image bytes do not become product or tooling attribution.

中文：确保图像字节完全相同仍不会被宣称为同产品或同模具；图像比较只提供筛选线索。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKIT_ROOT / "src"))

from factorytrace.compare import compare_images  # noqa: E402


class V2MediaTests(unittest.TestCase):
    def test_exact_file_does_not_claim_same_product_or_tooling(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference.png"
            Image.new("RGB", (32, 32), "white").save(reference)
            output = root / "comparison.csv"
            row = compare_images(reference, [reference], output, workers=1)[0]
            self.assertEqual(row["automated_media_relation"], "same_file")
            self.assertIn("not_assessed", row["physical_product_inference"])
            self.assertIn("tooling", row["physical_product_inference"])


if __name__ == "__main__":
    unittest.main()
