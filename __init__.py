"""
PYthon PREFrences or pypref is a python implementation to creating application's 
configuration, preferences or settings file and dynamically interacting, updating and 
pulling them. Most applications have default preferences and in general those are
created and stored in a text file (.ini, xml, json, etc). At some point preferences 
are pulled and updated by the application and/or users.
pypref is especially designed to take care of this task automatically and make 
programming application's preferences more desirable. 
In addition, pypref allows creating dynamic preferences that will be evaluated real
time. This becomes handy in plethora of applications for authentication, automatic 
key generation, etc.

Installation guide:
===================
pypref is a pure python 2.7.x module that needs no particular installation. One can either 
fork pypref's `github repository <https://github.com/bachiraoun/pypref/>`_ and copy the 
package to python's site-packages or use pip as the following:


.. code-block:: console
    
    
        pip install pypref
        

Package Functions:
==================
"""
from __pkginfo__ import __version__, __author__, __email__, __onlinedoc__, __repository__, __pypi__
from Preferences import Preferences, SinglePreferences

def get_version():
    """Get pypref's version number."""
    return __version__ 

def get_author():
    """Get pypref's author's name."""
    return __author__     
 
def get_email():
    """Get pypref's author's email."""
    return __email__   
    
def get_doc():
    """Get pypref's official online documentation link."""
    return __onlinedoc__       
    
def get_repository():
    """Get pypref's official online repository link."""
    return __repository__        
    
def get_pypi():
    """Get pypref pypi's link."""
    return __pypi__   
    
    
         