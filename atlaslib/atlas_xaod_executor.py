# Executor and code for the ATLAS xaod input files
import tempfile
from shutil import copyfile
import os
from urllib.parse import urlparse

import pandas as pd
import uproot

class atlas_xaod_executor:
    def __init__ (self, dataset):
        self._ds = dataset

    def copy_template_file(self, template_file, final_dir):
        'Copy a file to a final directory'
        name = os.path.basename(template_file)
        copyfile(template_file, final_dir + '/' + name)

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """
        # Create a temp directory in which we can run everything.
        #with tempfile.TemporaryDirectory() as local_run_dir:
        local_run_dir = tempfile.mkdtemp()

        # Next, copy over all the template files
        template_dir = "./R21Code"
        self.copy_template_file(template_dir + '/ATestRun_eljob.py', local_run_dir)
        self.copy_template_file(template_dir + '/package_CMakeLists.txt', local_run_dir)
        self.copy_template_file(template_dir + '/query.cxx', local_run_dir)
        self.copy_template_file(template_dir + '/query.h', local_run_dir)
        self.copy_template_file(template_dir + '/runner.sh', local_run_dir)

        # Next, build the control python files by scanning the AST for what is needed

        # Build the C++ file

        # Now use docker to run this mess
        print (self._ds)
        (_, netloc, path, _, _, _) = urlparse(self._ds)
        datafile = netloc + path
        datafile_dir = os.path.dirname(datafile)

        docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(local_run_dir, datafile_dir)
        os.system(docker_cmd)

        # Extract the result.
        output_file = "file://{0}/data.root".format(local_run_dir)
        data_file = uproot.open(output_file)
        df = data_file["analysis"].pandas.df()
        return df
