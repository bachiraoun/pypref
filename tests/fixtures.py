# -*- coding: utf-8 -*-

import sys
import tempfile

# for Python 3.2+, there is a TemporaryDirectory class defined
# a class substitute is proposed for lower versions.

if sys.version_info>(3,2):
    from tempfile import TemporaryDirectory
else:
    import shutil

    class TemporaryDirectory:
        def __init__(self):
            self.name = tempfile.mkdtemp()

        def cleanup(self):
            if self.name:
                shutil.rmtree(self.name)
                self.name = None

        def __del__(self):
            self.cleanup()
