# Event stream from ATLAS
from clientlib.EventStream import EventStream
from xAODlib.atlas_xaod_executor import atlas_xaod_executor
from xAODlib.cpp_representation import cpp_rep_base, cpp_variable, cpp_collection
import ast
import xAODlib.expression_ast as expression_ast
import xAODlib.statement as statement


class AtlasXAODFileStream(ast.AST):
    r"""
    An AST node that represents the event source.
    """

    def __init__(self, ds_url):
        self.dataset_url = ds_url

    def get_executor(self):
        return atlas_xaod_executor(self.dataset_url)


class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """

    def __init__(self, evt_stream):
        EventStream.__init__(self, AtlasXAODFileStream(evt_stream._url))
