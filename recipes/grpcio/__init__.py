from pythonforandroid.recipe import PythonRecipe
import os
import shutil

class GrpcioRecipe(PythonRecipe):
    version = '1.48.2'
    depends = []
    call_hostpython_via_targetpython = False

    def download_if_necessary(self):
        # Do nothing: skip download step
        pass

    def build_arch(self, arch):
        # Copy the dummy grpc.py to the site-packages directory
        dummy_grpc = os.path.join(self.get_recipe_dir(), 'grpc.py')
        target_dir = os.path.join(self.ctx.get_python_install_dir(arch.arch), 'site-packages')
        os.makedirs(target_dir, exist_ok=True)
        shutil.copyfile(dummy_grpc, os.path.join(target_dir, 'grpc.py'))

recipe = GrpcioRecipe() 