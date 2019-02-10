# A stream of some object

class ObjectStream:
    def __init__(self, parent):
        r"""
        Each node in an AST knows about its parent, so you can track all the way back.
        """
        self._parent = parent
        pass
    
    
    def SelectMany(self, func):
        r"""
        The user wants to unroll a collection. This func needs to:
        1. Figure out what needs to be done to get at the collection
        2. Return a stream of new objects.
        """

        return ObjectStream(self)

    def Calibrate(self):
        r"""
        Performs calibration on a stream of objects. I'd say this belonged in a
        client lib.
        """
        return ObjectStream(self)

    def Select(self, f):
        r"""
        User wants to transform a single object at a time in this stream.
        """
        return ObjectStream(self)

    def AsPandasDF(self):
        r"""
        Return a pandas dataframe. We do this by running the conversion.
        """

        # We do this by first generating a simple ROOT file, then loading it into a dataframe with
        # uproot.
        return self.AsROOTFile().AsPandasDFFromROOTFile()

    def AsROOTFile(self):
        r"""
        Terminal - take the AST and return a root file.
        """

        return ObjectStream(self)

    def AsPandasDFFromROOTFile(self):
        r"""
        Return a pandas df frame from the root file.
        """

        return ObjectStream(self)

    def value(self):
        r"""
        Trigger the evaluation of the AST.
        """

        exe = self.get_executor()
        return exe.evaluate(self)

    def get_executor(self):
        r"""
        Get the executor for this AST. We have to climb back all the way up the
        stream to find it.
        """

        return self._parent.get_executor()