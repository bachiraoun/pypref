# -*- coding: utf-8 -*-
"""
Usage:
======
This example shows how to use pypref.


.. code-block:: python

        from __future__ import print_function
        from pypref import Preferences

        #  create preferences instance
        pref = Preferences(filename="preferences_test.py")

        # create preferences dict example
        pdict = {'preference 1': 1, 12345: 'I am a number'}

        # set preferences. This would automatically create preferences_test.py
        # in your home directory. Go and check it.
        pref.set_preferences(pdict)

        # lets update the preferences. This would automatically update
        # preferences_test.py file, you can verify that.
        pref.update_preferences({'preference 1': 2})

        # lets get some preferences. This would return the value of the preference if
        # it is defined or default value if it is not.
        print(pref.get('preference 1'))

        # In some cases we must use raw strings. This is most likely needed when
        # working with paths in a windows systems or when a preference includes
        # especial characters. That's how to do it ...
        pref.update_preferences({'my path': 'C:\\\\Users\\\\Me\\\\Desktop'})

        # multi-line strings can also be used as values
        multiline=\"\"\"this is a
        multi-line
        value
        \"\"\"
        pref.update_preferences({'multiline preference': multiline})

        # Sometimes preferences to change dynamically or to be evaluated real time.
        # This also can be done by using dynamic property. In this example password
        # generator preference is set using uuid module. dynamic dictionary
        # must include all modules name that must be imported upon evaluating
        # a dynamic preference
        pre = {'password generator': "str(uuid.uuid1())"}
        dyn = {'password generator': ['uuid',]}
        pref.update_preferences(preferences=pre, dynamic=dyn)

        # lets pull 'password generator' preferences twice and notice how
        # passwords are different at every pull
        print(pref.get('password generator'))
        print(pref.get('password generator'))

        # those preferences can be accessed later. Let's simulate that by creating
        # another preferences instances which will automatically detect the
        # existance of a preferences file and connect to it
        newPref = Preferences(filename="preferences_test.py")

        # let's print 'my path' preference
        print(newPref.get('my path'))
        print(newPref.get('multiline preference'))





Preferences main module:
========================
"""
# standard library imports
import copy
import importlib
import os
import re
import sys
import tempfile
import warnings
from collections import OrderedDict

# pypref package information imports
# from .__pkginfo__ import __version__

# This is python 3
str = str
long = int
unicode = str
bytes = bytes
basestring = str

try:
    from pathlib import Path as pPath
except Exception as err:
    pPath = None.__class__


def _fix_path_sep(path):
    if os.sep == '\\':
        path = re.sub(r'([\\])\1+', r'\1', path).replace('\\', '\\\\')
    return path


def resolve_path(path, fixSep=True, allowNone=True):
    """get path resolved as a string.

    :Parameters:
        #. path (None, string, pathlib.Path): If string, user expanded path will
           be returned. If pathlib.Path is given, resolved string will be
           returned.
        #. fixSep (boolean): if os.sep is '\\',  normalize will replace
          '\\' with '\\\\'

    :Returns:
        #. result (None, string): None is returned if path is None, string
           is returned otherwise
    """
    if path is not None:
        if isinstance(path, str):
            path = os.path.expanduser(path)
            if fixSep:
                path = _fix_path_sep(path)
        else:
            assert isinstance(path, pPath), "Given path must be None, string or pathlib.Path instance"
            path = str(path.resolve())
    elif not allowNone:
        raise Exception("path must be given")
    return path


class Preferences(object):
    """
    This is pypref main preferences class definition. This class is used to create, load
    and update application's preferences dictionary in memory and in file.
    At initialization, a preferences dictionary will be pulled from the given directory
    and filename if existing. Otherwise, preferences file will be created and preferences
    dictionary will be initialized to an empty dictionary. Preferences can be accessed
    like any python dictionary by slicing a key preference [key] or by using get method.

    When used in a python application, it is advisable to use Preferences singleton
    implementation and not Preferences itself.
    if no overloading is needed one can simply import the singleton as the following:

    .. code-block:: python

        from pypref import SinglePreferences as Preferences



    Recommended overloading implementation, this is how it could be done:

    .. code-block:: python

        from pypref import SinglePreferences as PREF

        class Preferences(PREF):
            # *args and **kwargs can be replace by fixed arguments
            def custom_init(self, *args, **kwargs):
                # hereinafter any further instanciation can be coded



    In case overloading __init__ is needed, this is how it could be done:

    .. code-block:: python

        from pypref import SinglePreferences as PREF

        class Preferences(PREF):
            # custom_init will still be called in super(Preferences, self).__init__(*args, **kwargs)
            def __init__(self, *args, **kwargs):
                if self._isInitialized: return
                super(Preferences, self).__init__(*args, **kwargs)
                # hereinafter any further instanciation can be coded


    :Parameters:
        #. directory (None, path): The directory where to create preferences file.
           If None is given, preferences will be create in user's home directory.
        #. filename (string): The preferences file name.
        #. \*args (): This is used to send non-keyworded variable length argument
           list to custom initialize. args will be parsed and used in custom_init method.
        #. \**kwargs (): This allows passing keyworded variable length of arguments to
           custom_init method. kwargs can be anything other than 'directory' and
           'filename'.

    **N.B. args and kwargs are not used by __init__ method but passed to custom_init
    at the end of initialization. custom_init method is an empty method that can be
    overloaded**
    """

    def __init__(self, directory=None, filename="preferences.py", *args, **kwargs):
        self.__set_directory(directory=directory)
        self.__set_filename(filename=filename)
        # load existing or create file
        self.__preferences = {}
        self.__dynamic = {}
        self.__load_or_create()
        # custom initialize
        self.custom_init(*args, **kwargs)

    def __str__(self):
        return self.__get_lines(preferences=self.__preferences, dynamic=self.__dynamic)

    def __getitem__(self, key):
        pref = dict.__getitem__(self.__preferences, key)
        dyn = self.__dynamic.get(key, [])
        # valuate preference
        if len(dyn):
            try:
                for lib in dyn:
                    locals()[lib] = __import__(lib)
            except Exception as e:
                raise Exception("Unable to import module '%s' for preference '%s' evaluation (e)" % (lib, pref, e))
            try:
                pref = eval(pref)
            except Exception as e:
                raise Exception("Unable to evaluate preference '%s' (%s)" % (key, e))
        return pref

    def __set_directory(self, directory):
        directory = resolve_path(directory)
        if directory is None:
            directory = os.path.expanduser('~')
        # try to set directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs(directory)
        # check if a directory is writable
        try:
            testfile = tempfile.TemporaryFile(dir=directory)
            testfile.close()
        except Exception as e:
            raise Exception("Given directory '%s' is not a writable directory." % directory)
        # set directory
        self.__directory = _fix_path_sep(directory)  # directory

    def __set_filename(self, filename):
        filename = resolve_path(filename)
        assert isinstance(filename, basestring), "filename must be a string, '%s' is given." % filename
        filename = str(filename)
        assert os.path.basename(filename) == filename, "Given filename '%s' is not valid. \
A valid filename must not contain especial characters or operating system separator which is '%s' in this case." % (
        filename, os.sep)
        if not filename.endswith('.py'):
            filename += '.py'
            warnings.warn("'.py' appended to given filename '%s'" % filename)
        self.__filename = _fix_path_sep(filename)  # filename

    def __load_or_create(self):
        fullpath = self.fullpath
        exists = os.path.isfile(fullpath)  # this is not case-sensitive !!!
        if exists:
            module_name = os.path.basename(fullpath)
            spec = importlib.util.spec_from_loader(module_name,
                                                   importlib.machinery.SourceFileLoader(module_name, fullpath))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[module_name] = module

            # check whether it's a pypref module
            try:
                version = module.__pypref_version__
                preferences = module.preferences
            except Exception as e:
                raise Exception("Existing file '%s' is not a pypref file (%s)" % (fullpath, e))
            # try importing dynamic. Implemented started from version 2.0.0
            try:
                dynamic = module.dynamic
            except:
                dynamic = {}
            # check preferences
            assert isinstance(preferences, dict), "Existing file '%s' is not a pypref file " % fullpath
            assert isinstance(dynamic, dict), "Existing file '%s' is not a pypref file " % fullpath
            self.__preferences = preferences
            self.__dynamic = dynamic
        else:
            self.__dump_file(preferences={}, dynamic={})
            self.__preferences = {}
            self.__dynamic = {}

    def __get_normalized_string(self, s):
        return str(repr(s))

    def __get_lines(self, preferences, dynamic):
        # TODO: redo tho version so it dynamically takes the info
        # write preferences
        lines = "# This file is an automatically generated pypref preferences file. \n\n"
        # lines += "__pypref_version__ = '%s' \n\n" % (__version__,)
        lines += "__pypref_version__ = '4.0.0' \n\n"
        lines += "##########################################################################################\n"
        lines += "###################################### PREFERENCES #######################################\n"
        if isinstance(preferences, OrderedDict):
            lines += "from collections import OrderedDict" + "\n"
            lines += "preferences = OrderedDict()" + "\n"
        else:
            lines += "preferences = {}" + "\n"
        ###### get maximum key length
        maxLen = [len(str(k)) for k in preferences.keys()]
        if len(maxLen):
            maxLen = max(maxLen)
        else:
            maxLen = 0
        maxLen += len('preferences[""]')
        # write preferences
        for k, v in preferences.items():
            if isinstance(k, basestring):
                k = self.__get_normalized_string(k)
            if isinstance(v, basestring):
                v = self.__get_normalized_string(v)
            lines += ("preferences[%s]" % (k,)).ljust(maxLen) + " = %s\n" % (v,)
        ###### write dynamic
        lines += "\n"
        lines += "##########################################################################################\n"
        lines += "############################## DYNAMIC PREFERENCES MODULES ###############################\n"
        if isinstance(preferences, OrderedDict):
            lines += "from collections import OrderedDict" + "\n"
            lines += "dynamic = OrderedDict()" + "\n"
        else:
            lines += "dynamic = {}" + "\n"
        # get maximum key length
        maxLen = [len(str(k)) for k in dynamic.keys()]
        if len(maxLen):
            maxLen = max(maxLen)
        else:
            maxLen = 0
        maxLen += len('dynamic[""]')
        for k, v in dynamic.items():
            if isinstance(k, basestring):
                k = self.__get_normalized_string(k)
            if isinstance(v, basestring):
                v = self.__get_normalized_string(v)
            lines += ("dynamic[%s]" % (k,)).ljust(maxLen) + " = %s\n" % (v,)
        return lines

    def __dump_file(self, preferences, dynamic, temp=False):
        try:
            lines = self.__get_lines(preferences=preferences, dynamic=dynamic)
        except Exception as error:
            raise Exception("unable to create preferences data. (%s)" % error)
        # dump file
        try:
            if temp:
                with tempfile.NamedTemporaryFile(mode='w+b', dir=tempfile._get_default_tempdir(), delete=True) as fd:
                    fd.write(lines.encode('utf-8'))
            else:
                with open(self.fullpath, 'wb') as fd:
                    fd.write(lines.encode('utf-8'))
        except Exception as error:
            raise Exception("unable to write preferences%sfile. (%s)" % (' temporary ' if temp else ' ', error))

    @property
    def directory(self):
        """Preferences file directory."""
        return copy.deepcopy(self.__directory)

    @property
    def filename(self):
        """Preferences file name."""
        return copy.deepcopy(self.__filename)

    @property
    def fullpath(self):
        """Preferences file full path."""
        return _fix_path_sep(os.path.join(self.__directory, self.__filename))

    @property
    def preferences(self):
        """Preferences dictionary copy."""
        return copy.deepcopy(self.__preferences)

    @property
    def dynamic(self):
        """Dynamic dictionary copy."""
        return copy.deepcopy(self.__dynamic)

    def custom_init(self, *args, **kwargs):
        """
        Custom initialize abstract method. This method will be called  at the end of
        initialization. This method needs to be overloaded to custom initialize
        Preferences instances.

        :Parameters:
            #. \*args (): This is used to send non-keyworded variable length argument
               list to custom initialize.
            #. \**kwargs (): This allows passing keyworded variable length of arguments to
               custom_init method. kwargs can be anything other than 'directory' and
               'filename'.
        """
        pass

    def get(self, key, default=None):
        """
        Get the preferences value for the given key.
        If key is not available then returns then given default value.

        :Parameters:
            #. key (object): The Key to be searched in the preferences.
            #. default (object): The Value to be returned in case key does not exist.

        :Returns:
            #. value (object): The value of the given key or given default value is
               key does not exist.
        """
        pref = self.__preferences.get(key, default)
        dyn = self.__dynamic.get(key, [])
        # valuate preference
        if len(dyn):
            try:
                for lib in dyn:
                    locals()[lib] = __import__(lib)
            except Exception as e:
                raise Exception("Unable to import module '%s' for preference '%s' evaluation (e)" % (lib, pref, e))
            try:
                pref = eval(pref)
            except Exception as e:
                raise Exception("Unable to evaluate preference '%s'" % key)
        # return
        return pref

    def check_preferences(self, preferences):
        """
        This is an abstract method to be overloaded if needed.
        All preferences setters such as set_preferences and update_preferences
        call check_preferences prior to setting anything. This method returns
        a check flag and a message, if the flag is False, the message is raised
        as an error like the following:

        .. code-block:: python

            flag, m = self.check_preferences(preferences)
            assert flag, m


        :Parameters:
            #. preferences (dictionary): The preferences dictionary.

        :Returns:
            #. flag (boolean): The check flag.
            #. message (string): The error message to raise.

        """
        return True, ""

    def set_default(self, preferences, dynamic=None):
        """
        Add preferences if not defined otherwise no action is executed

        :Parameters:
            #. preferences (None, dictionary): The preferences dictionary.
               If None dynamic dictionary won't be updated.
            #. dynamic (None, dictionary): The dynamic dictionary. If None dynamic
               dictionary won't be updated.
        """
        assert preferences is not None or dynamic is not None, "Both preferences and dynamic can't be None"
        reset = False
        # check dynamic
        if dynamic is None:
            newDynamic = self.__dynamic
        else:
            assert isinstance(dynamic, dict), "dynamic must be None or a dictionary"
            newDynamic = copy.deepcopy(self.__dynamic)
            for p in dynamic:
                if p not in newDynamic:
                    reset = True
                    newDynamic[p] = dynamic[p]
        # check prefererences
        if preferences is None:
            newPreferences = self.__preferences
        else:
            flag, m = self.check_preferences(preferences)
            assert flag, m
            assert isinstance(preferences, dict), "preferences must be None or a dictionary"
            newPreferences = copy.deepcopy(self.__preferences)
            for p in preferences:
                if p not in newPreferences:
                    reset = True
                    newPreferences[p] = preferences[p]
        # set preferences
        if reset:
            self.set_preferences(preferences=newPreferences, dynamic=newDynamic)

    def update_preferences(self, preferences, dynamic=None):
        """
        Add and update preferences with the given ones

        :Parameters:
            #. preferences (None, dictionary): The preferences dictionary.
               If None dynamic dictionary won't be updated.
            #. dynamic (None, dictionary): The dynamic dictionary. If None dynamic
               dictionary won't be updated.
        """
        assert preferences is not None or dynamic is not None, "Both preferences and dynamic can't be None"
        reset = False
        # check dynamic
        if dynamic is None:
            newDynamic = self.__dynamic
        else:
            assert isinstance(dynamic, dict), "dynamic must be None or a dictionary"
            newDynamic = copy.deepcopy(self.__dynamic)
            for p in dynamic:
                v = dynamic[p]
                if p not in newDynamic or newDynamic.get(p, None) != v:
                    reset = True
                    newDynamic[p] = v
        # check prefererences
        if preferences is None:
            newPreferences = self.__preferences
        else:
            flag, m = self.check_preferences(preferences)
            assert flag, m
            assert isinstance(preferences, dict), "preferences must be None or a dictionary"
            newPreferences = copy.deepcopy(self.__preferences)
            for p in preferences:
                v = preferences[p]
                if p not in newPreferences or newPreferences.get(p, None) != v:
                    reset = True
                    newPreferences[p] = v
        # set preferences
        if reset:
            self.set_preferences(preferences=newPreferences, dynamic=newDynamic)

    def set_preferences(self, preferences, dynamic=None):
        """
        Set preferences and write preferences file by erasing any existing one.

        :Parameters:
            #. preferences (dictionary): The preferences dictionary.
            #. dynamic (None, dictionary): The dynamic dictionary. If None dynamic
               dictionary won't be updated.
        """
        flag, m = self.check_preferences(preferences)
        assert flag, m
        assert isinstance(preferences, dict), "preferences must be a dictionary"
        if dynamic is None:
            # try dumping to temp file first
            self.__dump_file(preferences=preferences, dynamic=self.__dynamic, temp=True)
            try:
                self.__dump_file(preferences=preferences, dynamic=self.__dynamic, temp=True)
            except Exception as e:
                raise Exception("Unable to dump temporary preferences file (%s)." % e)
            # dump to file
            try:
                self.__dump_file(preferences=preferences, dynamic=self.__dynamic, temp=False)
            except Exception as e:
                raise Exception(
                    "Unable to dump preferences file (%s). Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged." % e)
        else:
            oldPreferences = self.__preferences
            self.__preferences = preferences
            try:
                self.set_dynamic(dynamic=dynamic)
            except Exception as e:
                self.__preferences = oldPreferences
                raise Exception(
                    "Unable to set dynamic from set_preferences method. Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged." % e)
        # set preferences
        self.__preferences = preferences

    def set_dynamic(self, dynamic):
        """
        Set dynamic and write preferences file by erasing any existing one.

        :Parameters:
            #. dynamic (dictionary): The dynamic dictionary.
        """
        assert isinstance(dynamic, dict), "dynamic must be a dictionary"
        D = {}
        for k, v in dynamic.items():
            if not k in self.__preferences:
                warnings.warn("dynamic key '%s' is discarded as it's not a valid preference" % k)
                continue
            if v is not None:
                assert isinstance(v, (
                list, set, tuple)), "dynamic dictionary values can be None or a list of importable modules"
                assert len(set(v)) == len(v), "dynamic dictionary values are redundant for preference '%s'" % k
                for m in v:
                    assert isinstance(m, basestring), "dynamic dictionary values must be a list of strings"
            else:
                v = []
            D[k] = tuple(v)
        dynamic = D
        # try dumping to temp file first
        try:
            self.__dump_file(preferences=self.__preferences, dynamic=dynamic, temp=True)
        except Exception as e:
            raise Exception("Unable to dump temporary preferences file. Preferences are unchanged. (%s)" % e)
        # dump to file
        try:
            self.__dump_file(preferences=self.__preferences, dynamic=dynamic, temp=False)
        except Exception as e:
            raise Exception(
                "Unable to dump preferences file (%s). Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged." % e)
        # set dynamic preferences
        self.__dynamic = dynamic

    def reload(self, raiseError=False):
        """
        reload preferences from file

        :Parameters:
            #. raiseError (bool): whether to raise error if any occured
        """
        assert isinstance(raiseError, bool), "raiseError must be boolean"
        try:
            oldPreferences = self.__preferences
            oldDynamic = self.__dynamic
            self.__load_or_create()
        except Exception as err:
            self.__preferences = oldPreferences
            self.__dynamic = oldDynamic
            if raiseError:
                raise Exception("Unable to reload preferences (%s)" % err)


class SinglePreferences(Preferences):
    """
    This is singleton implementation of Preferences class.
    """
    __thisInstance = None

    def __new__(cls, *args, **kwargs):
        if cls.__thisInstance is None:
            cls.__thisInstance = super(SinglePreferences, cls).__new__(cls)
            cls.__thisInstance._isInitialized = False
        return cls.__thisInstance

    def __init__(self, *args, **kwargs):
        if (self._isInitialized): return
        # initialize
        super(SinglePreferences, self).__init__(*args, **kwargs)
        # update flag
        self._isInitialized = True
