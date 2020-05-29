import unittest
import tempfile
from pypref import SinglePreferences as Preferences

class TestPreferencesMethods(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        p = Preferences(directory=self.d.name)
        p.set_preferences({'preset' : True})
        del p

    def test_loadexistingpref(self):
        p = Preferences(directory=self.d.name)
        self.assertTrue(p.get('preset',False))

    def tearDown(self):
        self.d.cleanup()

if __name__ == '__main__':
    unittest.main()
