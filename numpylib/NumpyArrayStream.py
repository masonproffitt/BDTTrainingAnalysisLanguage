# Event stream from numpy
import ast
from numpylib.numpy_array_executor import numpy_array_executor
from clientlib.ArrayStream import ArrayStream

class NumpySourceStream(ast.AST):
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source
        self.rep = 'base_array'

    def get_executor(self):
        return numpy_array_executor(self.dataset_source)

class NumpyArrayStream(ArrayStream):
    def __init__(self, array_dataset):
        ArrayStream.__init__(self, NumpySourceStream(array_dataset.dataset_source))
