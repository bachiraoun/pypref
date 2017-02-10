"""
Usage:
======
This example shows how to use pypref.


.. code-block:: python
    
        from pypref import Preferences
        
        #  create preferences instance
        pref = Preferences(filename="preferences_test.py")
        
        # create preferences dict example
        pdict = {'preference 1': 1,
                 12345: 'I am a number'}
        
        # set preferences. This would automatically create preferences_test.py 
        # in your home directory. Go and check it.
        pref.set_preferences(pdict)
        
        # let update the preferences. This would automatically update preferences_test.py
        # file, you can verify that. 
        pref.update_preferences({'preference 1': 2})
        
        # lets get some preferences. This would return the value of the preference if
        # it is defined or default value if it is not.
        print pref.get('preference 1')
        
        # In some cases we must use raw strings. This is most likely needed when
        # working with paths in a windows systems or when a preference includes
        # especial characters. That's how to do it ...
        pref.update_preferences({'my path': " r'C:\Users\Me\Desktop' "})
        
        # those preferences can be accessed later. Let's simulate that by creating
        # another preferences instances which will automatically detect the 
        # existance of a preferences file and connect to it
        newPref = Preferences(filename="preferences_test.py")
        
        # let's print 'my path' preference
        print newPref.get('my path')
        
        
        
        
Preferences main module:
========================
"""
# standard library imports
import sys, os, copy, tempfile
#from importlib import import_module
import imp
import warnings

# pypref package information imports
from __pkginfo__ import __version__


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
    
    
    
    In case overloading is needed, this is how it could be done:    
    
    .. code-block:: python
        
        from pypref import SinglePreferences as PREF
        
        class Preferences(PREF):
            def __init__(self, *args, **kwargs):
                if self._isInitialized: return
                super(Preferences, self).__init__(*args, **kwargs)
                # hereinafter any further instanciation can be coded
                
         
    :Parameters:
        #. directory (None, path): The directory where to create preferences file.
           If None is given, preferences will be create in user's home directory.
        #. filename (string): The preferences file name.
    """
    def __init__(self, directory=None, filename="preferences.py"):
        self.__set_directory(directory=directory)
        self.__set_filename(filename=filename)
        # load existing or create file
        self.__load_or_create()
    
    def __getitem__(self, key):
        return dict.__getitem__(self.__preferences, key)
    
    def __set_directory(self, directory):
        if directory is None:
            directory = os.path.expanduser('~')
        else:
            assert os.path.isdir(directory), "Given directory '%s' is not an existing directory"%directory
        # check if a directory is writable
        try:
            testfile = tempfile.TemporaryFile(dir = directory)
            testfile.close()
        except Exception as e:
            raise Exception("Given directory '%s' is not a writable directory."%directory)
        # set directory
        self.__directory = directory
            
    def __set_filename(self, filename): 
        assert isinstance(filename, basestring), "filename must be a string, '%s' is given."%filename
        filename = str(filename)
        assert os.path.basename(filename) == filename, "Given filename '%s' is not valid. \
A valid filename must not contain especial characters or operating system separator which is '%s' in this case."%(filename, os.sep)
        if not filename.endswith('.py'):
            filename += '.py'
            warnings.warn("'.py' appended to given filename '%s'"%filename)
        self.__filename = filename
    
    def __load_or_create(self):
        fullpath = self.fullpath
        if os.path.isfile(fullpath):
            (path, name) = os.path.split(fullpath) # to use imp instead of importlib
            (name, ext)  = os.path.splitext(name)  # to use imp instead of importlib
            (file, filename, data) = imp.find_module(name, [path]) # to use imp instead of importlib
            # try to import as python module
            try:
                #mod = import_module(fullpath)
                mod = imp.load_module(name, file, filename, data)
            except Exception as e:
                raise Exception("Existing file '%s' is not a python importable file (%s)"%(fullpath, e))
            # check whether it's a pypref module
            try:
                version     = mod.__pypref_version__
                preferences = mod.preferences
            except Exception as e:
                raise Exception("Existing file '%s' is not a pypref file (%s)"%(fullpath, e))
            # check preferences
            assert isinstance(preferences, dict), "Existing file '%s' is not a pypref file (%s)"%(fullpath, e)
            self.__preferences = preferences
        else:
            self.__dump_file(preferences = {})  
            self.__preferences = {}      
            
    def __get_normalized_string(self, s):
        stripped = s.strip()
        if not stripped.startswith('"') and not stripped.endswith('"'):
            if not stripped.startswith("'") and not stripped.endswith("'"):
                if "'" in s:
                    s = '"%s"'%s
                else:
                    s = "'%s'"%s
        return s
                         
    def __dump_file(self,  preferences, temp=False):
        if temp:
            try:
                fd = tempfile.NamedTemporaryFile(dir=tempfile._get_default_tempdir(), delete=True)
            except Exception as e:
                raise Exception("unable to create preferences temporary file. (%s)"%e)
        else:
            # try to open preferences file
            try:
                fd = open(self.fullpath, 'w')
            except Exception as e:
                raise Exception("Unable to open preferences file '%s."%self.fullpath)
        # write preferences
        lines  = "# This file is an automatically generated pypref preferences file. \n\n" 
        lines += "__pypref_version__ = '%s' \n\n"%__version__ 
        lines += "preferences = {}" + "\n"
        for k, v in preferences.items():
            if isinstance(k, basestring):
                k = self.__get_normalized_string(k)
            if isinstance(v, basestring):
                v = self.__get_normalized_string(v)
            lines += "preferences[%s] = %s\n"%(k, v)
        # write lines  
        try:     
            fd.write(lines) 
        except Exception as e:
            raise Exception("Unable to write preferences to file '%s."%self.fullpath)
        # close file
        fd.close()
    
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
        return os.path.join(self.__directory, self.__filename)
    
    @property
    def preferences(self):
        """Preferences dictionary copy."""
        return copy.deepcopy(self.__preferences)
            
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
        return self.__preferences.get(key, default)
        
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
        
    def set_preferences(self, preferences):
        """
        Set preferences and write preferences file by erasing any existing one.
        
        :Parameters:
            #. preferences (dictionary): The preferences dictionary.
        """
        flag, m = self.check_preferences(preferences)
        assert flag, m
        assert isinstance(preferences, dict), "preferences must be a dictionary"
        # try dumping to temp file first
        try:
            self.__dump_file(preferences, temp=True)
        except Exception as e:
            raise Exception("Unable to dump temporary preferences file (%s)"%e)
        # dump to file
        try:
            self.__dump_file(preferences, temp=False)
        except Exception as e:
            raise Exception("Unable to dump preferences file (%s). Preferences file can be corrupt, but in memory stored preferences are still available using and accessible using preferences property."%e)
        # set preferences
        self.__preferences = preferences
    
    def update_preferences(self, preferences):
        """
        Update preferences and update preferences file.
        
        :Parameters:
            #. preferences (dictionary): The preferences dictionary.
        """
        flag, m = self.check_preferences(preferences)
        assert flag, m
        assert isinstance(preferences, dict), "preferences must be a dictionary"
        newPreferences = self.preferences
        newPreferences.update(preferences)
        # set new preferences
        self.set_preferences(newPreferences)
        
            
            
class SinglePreferences(Preferences):
    """
    This is singleton implementation of Preferences class.
    """
    __thisInstance = None
    def __new__(cls, *args, **kwds):
        if cls.__thisInstance is None:
            cls.__thisInstance = super(SinglePreferences,cls).__new__(cls)
            cls.__thisInstance._isInitialized = False
        return cls.__thisInstance
    
    def __init__(self, *args, **kwargs):      
        if (self._isInitialized): return
        # initialize
        super(SinglePreferences, self).__init__(*args, **kwargs)
        # update flag
        self._isInitialized = True
        


        
                    
            
            
            
        
        
        