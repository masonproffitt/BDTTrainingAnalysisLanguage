# A stream of some object
import pandas as pd

class ObjectStream:
    def __init__(self):
        pass
    
    
    def SelectMany(self, func):
        r"""
        The user wants to unroll a collection. This func needs to:
        1. Figure out what needs to be done to get at the collection
        2. Return a stream of new objects.
        """

        return ObjectStream()

    def Calibrate(self):
        r"""
        Performs calibration on a stream of objects. I'd say this belonged in a
        client lib.
        """
        return ObjectStream()

    def Select(self, f):
        r"""
        User wants to transform a single object at a time in this stream.
        """
        return ObjectStream()

    def AsPandasDF(self):
        r"""
        Return a pandas dataframe
        """
        return pd.DataFrame()