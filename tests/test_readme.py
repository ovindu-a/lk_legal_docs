import unittest

from lld import ReadMe


class TestCase(unittest.TestCase):
    def test_readme(self):
        ReadMe().build()
