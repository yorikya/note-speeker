from pythonforandroid.recipe import PythonRecipe

class PythonBidiRecipe(PythonRecipe):
    version = '0.4.2'
    url = 'https://files.pythonhosted.org/packages/source/p/python-bidi/python-bidi-{version}.tar.gz'
    depends = []
    call_hostpython_via_targetpython = False

recipe = PythonBidiRecipe() 