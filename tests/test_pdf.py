import os
import unittest

from utils_future import PDF

TEST_PDF_PATH = os.path.join("tests", "test_data", "test.pdf")


class TestCase(unittest.TestCase):
    def test_compress(self):
        output_path = os.path.join(
            "tests", "test_data", "test-compressed.pdf"
        )
        if os.path.exists(output_path):
            os.remove(output_path)

        PDF.compress(TEST_PDF_PATH, output_path)

        size_before = os.path.getsize(TEST_PDF_PATH)
        size_after = os.path.getsize(output_path)

        self.assertEqual(size_before, 339_235)
        self.assertLess(size_after, size_before * 0.75)

        PDF.compress(output_path, output_path)
        size_after_again = os.path.getsize(output_path)
        self.assertLess(size_after_again, size_after * 1.1)
        self.assertGreater(size_after_again, size_after * 0.9)
