# Event stream from ATLAS
import ast
from RDFlib.ntup_executor import ntup_executor
from clientlib.EventStream import EventStream

class RDFFileStream(ast.AST):
    r"""
    An AST node that represents the event source.
    """
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source
        self.rep = 'RDFrep'

    def get_executor(self):
        return ntup_executor(self.dataset_source)


class RDFEventStream(EventStream):
    r"""
    A stream of events from an ntuple file.
    """
    def __init__(self, ntup_dataset):
        EventStream.__init__(self, RDFFileStream(ntup_dataset._url))