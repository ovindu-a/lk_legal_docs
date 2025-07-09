import unittest

from lld import ReadMe


class TestCase(unittest.TestCase):
    @unittest.skip("Modifies README.md")
    def test_readme(self):
        ReadMe().build()
