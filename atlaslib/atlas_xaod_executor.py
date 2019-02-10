# Executor and code for the ATLAS xaod input files
import pandas as pd

class atlas_xaod_executor:
    def bogus (self):
        print ("hi")

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """
        return pd.DataFrame()