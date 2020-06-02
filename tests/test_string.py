# -*- coding: utf-8 -*-

import unittest
import warnings
from pypref import Preferences
from .fixtures import TemporaryDirectory


class TestPreferencesStrings(unittest.TestCase):

    pref = {'string 1' : 'This is a string with interpolation{}',
            'string 2' : 'With single quote',
            'string 3' : "With double quote",
            'string 4' : """Multi-line
string""" }


class Test(unittest.TestCase):

    def setUp(self):
        self.d = TemporaryDirectory()
        p = Preferences(directory=self.d.name)
        p.set_preferences( TestPreferencesStrings.pref )

    def tearDown(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.d = None

    def test_interpolate_string(self):
        """test string interpolation"""
        p = Preferences(directory=self.d.name)
        self.assertEqual(p.get('string 1',"{}").format('!'),
                         TestPreferencesStrings.pref['string 1'].format('!'))

    def test_various_string_formats(self):
        """test various string formats"""
        p = Preferences(directory=self.d.name)

        for key,value in TestPreferencesStrings.pref.items():
            self.assertEqual(p.get(key,""), value)

if __name__ == '__main__':
    unittest.main(warnings=None)
