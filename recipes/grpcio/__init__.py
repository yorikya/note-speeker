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
        # Copy the dummy grpc package to the site-packages directory
        dummy_grpc_dir = os.path.join(self.get_recipe_dir(), 'grpc')
        target_dir = os.path.join(self.ctx.get_python_install_dir(arch.arch), 'site-packages', 'grpc')
        os.makedirs(target_dir, exist_ok=True)
        for filename in os.listdir(dummy_grpc_dir):
            src_file = os.path.join(dummy_grpc_dir, filename)
            dst_file = os.path.join(target_dir, filename)
            shutil.copyfile(src_file, dst_file)

recipe = GrpcioRecipe() 