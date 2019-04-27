import unittest

import xorgdata


class BaseTests(unittest.TestCase):
    def test_version(self):
        self.assertIsNotNone(xorgdata.__version__)
