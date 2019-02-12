# Executor and code for the ATLAS xaod input files
import tempfile
from shutil import copyfile
import os
from urllib.parse import urlparse
import jinja2

import pandas as pd
import uproot

class atlas_xaod_executor:
    def __init__ (self, dataset):
        self._ds = dataset

    def copy_template_file(self, j2_env, info, template_file, final_dir):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(info).dump(final_dir + '/' + template_file)

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """
        # First thing to do is to scan the ast for template replacement items.
        info={}
        ast.fill_template_dict(info)

        # Create a temp directory in which we can run everything.
        with tempfile.TemporaryDirectory() as local_run_dir:

            # Parse the dataset. Eventually, this needs to be normalized, but for now.
            (_, netloc, path, _, _, _) = urlparse(self._ds)
            datafile = netloc + path
            datafile_dir = os.path.dirname(datafile)
            datafile_name = os.path.basename(datafile)
            info['data_file_name'] = datafile_name

            # Next, copy over and fill the template files
            template_dir = "./R21Code"
            j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
            self.copy_template_file(j2_env, info, 'ATestRun_eljob.py', local_run_dir)
            self.copy_template_file(j2_env, info, 'package_CMakeLists.txt', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.cxx', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.h', local_run_dir)
            self.copy_template_file(j2_env, info, 'runner.sh', local_run_dir)

            # Next, build the control python files by scanning the AST for what is needed

            # Build the C++ file

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(local_run_dir, datafile_dir)
            os.system(docker_cmd)

            # Extract the result.
            output_file = "file://{0}/data.root".format(local_run_dir)
            data_file = uproot.open(output_file)
            df = data_file["analysis"].pandas.df()
            data_file._context.source.close()
            return df
