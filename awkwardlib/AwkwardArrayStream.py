# Event stream from awkward
import ast
from awkwardlib.awkward_array_executor import awkward_array_executor
from clientlib.ArrayStream import ArrayStream

class AwkwardSourceStream(ast.AST):
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source
        self.rep = 'base_awkward_array'

    def get_executor(self):
        return awkward_array_executor(self.dataset_source)

class AwkwardArrayStream(ArrayStream):
    def __init__(self, array_dataset):
        ArrayStream.__init__(self, AwkwardSourceStream(array_dataset.dataset_source))
