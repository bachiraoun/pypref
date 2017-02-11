"""
Usage:
======
This example shows how to use pypref.


.. code-block:: python
    
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
        print pref.get('preference 1')
        
        # In some cases we must use raw strings. This is most likely needed when
        # working with paths in a windows systems or when a preference includes
        # especial characters. That's how to do it ...
        pref.update_preferences({'my path': " r'C:\Users\Me\Desktop' "})
        
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
        print pref.get('password generator')
        print pref.get('password generator')
        
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
        #. *args (): This is used to send non-keyworded variable length argument 
           list to custom initialize. args will be parsed and used in custom_init method.
        #. **kwargs (): This allows passing keyworded variable length of arguments to
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
        self.__dynamic     = {}
        self.__load_or_create()
        # custom initialize
        self.custom_init( *args, **kwargs )
        
    
    def __getitem__(self, key):
        pref = dict.__getitem__(self.__preferences, key)
        dyn  = self.__dynamic.get(key, [])
        # valuate preference
        if len(dyn):
            try:
                for lib in dyn:
                    locals()[lib] = __import__(lib)
            except Exception as e:
                raise Exception("Unable to import module '%s' for preference '%s' evaluation (e)"%(lib,pref,e))
            try:
                pref = eval(pref)
            except Exception as e:
                raise Exception("Unable to evaluate preference '%s' (%s)"%(key,e))
        return pref
    
    def __set_directory(self, directory):
        if directory is None:
            directory = os.path.expanduser('~')
        # try to set directory if it doesn't exist
        if not os.path.exists(directory):
            os.makedirs( directory )
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
            # try importing dynamic. Implemented started from version 2.0.0
            try:
                dynamic = mod.dynamic
            except:
                dynamic = {}
            # check preferences
            assert isinstance(preferences, dict), "Existing file '%s' is not a pypref file (%s)"%(fullpath, e)
            assert isinstance(dynamic, dict),     "Existing file '%s' is not a pypref file (%s)"%(fullpath, e)
            self.__preferences = preferences
            self.__dynamic     = dynamic
        else:
            self.__dump_file(preferences = {}, dynamic = {})  
            self.__preferences = {}      
            self.__dynamic     = {}
            
    def __get_normalized_string(self, s):
        stripped = s.strip()
        if not stripped.startswith('"') and not stripped.endswith('"'):
            if not stripped.startswith("'") and not stripped.endswith("'"):
                if "'" in s:
                    s = '"%s"'%s
                else:
                    s = "'%s'"%s
        return s
                         
    def __dump_file(self, preferences, dynamic, temp=False):
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
        lines += "##########################################################################################\n"
        lines += "###################################### PREFERENCES #######################################\n"
        lines += "preferences = {}" + "\n"
        for k, v in preferences.items():
            if isinstance(k, basestring):
                k = self.__get_normalized_string(k)
            if isinstance(v, basestring):
                v = self.__get_normalized_string(v)
            lines += "preferences[%s] = %s\n"%(k, v)
        # write dynamic
        lines += "\n"
        lines += "##########################################################################################\n"
        lines += "############################## DYNAMIC PREFERENCES MODULES ###############################\n"
        lines += "dynamic = {}" + "\n"
        for k, v in dynamic.items():
            if isinstance(k, basestring):
                k = self.__get_normalized_string(k)
            if isinstance(v, basestring):
                v = self.__get_normalized_string(v)
            lines += "dynamic[%s] = %s\n"%(k, v)
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
    
    @property
    def dynamic(self):
        """Dynamic dictionary copy."""
        return copy.deepcopy(self.__dynamic)
    
    def custom_init(self, *args, **kwargs):
        """
        Custom initialize abstract method. This method will be called  at the end of 
        initialzation. This method needs to be overloaded to custom initialize 
        Preferences instances. 
        
        :Parameters:
            #. *args (): This is used to send non-keyworded variable length argument 
               list to custom initialize. 
            #. **kwargs (): This allows passing keyworded variable length of arguments to
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
        dyn  = self.__dynamic.get(key, [])
        # valuate preference
        if len(dyn):
            try:
                for lib in dyn:
                    locals()[lib] = __import__(lib)
            except Exception as e:
                raise Exception("Unable to import module '%s' for preference '%s' evaluation (e)"%(lib,pref,e))
            try:
                pref = eval(pref)
            except Exception as e:
                raise Exception("Unable to evaluate preference '%s'"%key)
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
            try:
                self.__dump_file(preferences=preferences, dynamic=self.__dynamic, temp=True)
            except Exception as e:
                raise Exception("Unable to dump temporary preferences file (%s)."%e)
            # dump to file
            try:
                self.__dump_file(preferences=preferences, dynamic=self.__dynamic, temp=False)
            except Exception as e:
                raise Exception("Unable to dump preferences file (%s). Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged."%e)
        else:
            oldPreferences     = self.__preferences
            self.__preferences = preferences
            try:
                self.set_dynamic(dynamic=dynamic)
            except Exception as e:
                self.__preferences = oldPreferences
                raise Exception("Unable to set dynamic from set_preferences method. Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged."%e)
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
        for k,v in dynamic.items():
            if not self.__preferences.has_key(k):
                warnings.warn("dynamic key '%s' is discarded as it's not a valid preference"%k)
                continue
            if v is not None:
                assert isinstance(v, (list,set,tuple)), "dynamic dictionary values can be None or a list of importable modules"
                assert len(set(v)) == len(v), "dynamic dictionary values are redundant for preference '%s'"%k
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
            raise Exception("Unable to dump temporary preferences file. Preferences are unchanged. (%s)"%e)
        # dump to file
        try:
            self.__dump_file(preferences=self.__preferences, dynamic=dynamic, temp=False)
        except Exception as e:
            raise Exception("Unable to dump preferences file (%s). Preferences file can be corrupt, but in memory stored preferences are still available and accessible using preferences property. Preferences are unchanged."%e)
        # set dynamic preferences
        self.__dynamic = dynamic
        
    def update_preferences(self, preferences, dynamic=None):
        """
        Update preferences and dynamic dictionaries and update preferences file.
        
        :Parameters:
            #. preferences (dictionary): The preferences dictionary.
            #. dynamic (dictionary): The dynamic dictionary. If None is given, dynamic
               dictionary won't get updated
        """
        flag, m = self.check_preferences(preferences)
        assert flag, m
        assert isinstance(preferences, dict), "preferences must be a dictionary"
        newPreferences = self.preferences
        newPreferences.update(preferences)
        if dynamic is not None:
            assert isinstance(dynamic, dict), "dynamic must be a dictionary"
            dyn = self.dynamic
            dyn.update(dynamic)
            dynamic = dyn
        # set new preferences
        self.set_preferences(newPreferences, dynamic=dynamic)

                
            
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
        


        
                    
            
            
            
        
        
        