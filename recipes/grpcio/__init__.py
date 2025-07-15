from pythonforandroid.recipe import PythonRecipe
import os

class GrpcioRecipe(PythonRecipe):
    version = '1.48.2'
    url = 'https://example.com/grpcio-{version}.tar.gz'  # Dummy URL, not used
    depends = []
    call_hostpython_via_targetpython = False

    def build_arch(self, arch):
        # Copy the dummy grpc.py to the site-packages directory
        dummy_grpc = os.path.join(self.get_recipe_dir(), 'grpc.py')
        target_dir = os.path.join(self.ctx.get_python_install_dir(arch.arch), 'site-packages')
        self.ctx.copy_file(dummy_grpc, os.path.join(target_dir, 'grpc.py'))

recipe = GrpcioRecipe() 