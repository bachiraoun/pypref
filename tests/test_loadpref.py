# -*- coding: utf-8 -*-

import unittest
from pypref import Preferences
from tempfile import TemporaryDirectory


class TestPreferencesMethods(unittest.TestCase):

    def setUp(self):
        self.d = TemporaryDirectory()
        p = Preferences(directory=self.d.name)
        p.set_preferences({'preset': True})

    def test_loadexistingpref(self):
        """test persistence of preferences file"""
        p = Preferences(directory=self.d.name)
        self.assertTrue(p.get('preset', False))

    def tearDown(self):
        self.d.cleanup()


if __name__ == '__main__':
    unittest.main()
