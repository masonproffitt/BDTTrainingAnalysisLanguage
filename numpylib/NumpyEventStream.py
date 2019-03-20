# Event stream from numpy
import ast
from numpylib.numpy_array_executor import numpy_array_executor
from clientlib.EventStream import EventStream

class NumpyArrayStream(ast.AST):
    """
    An AST node that represents the event source.
    """

    def __init__(self, ds):
        self.dataset = ds
        self.rep = "numpy_array_stream"

    def get_executor(self):
        return numpy_array_executor(self.dataset)

class NumpyEventStream(EventStream):
    """
    A stream of events from an ATLAS xAOD file.
    """

    def __init__(self, evt_stream):
        EventStream.__init__(self, NumpyArrayStream(evt_stream._url))
