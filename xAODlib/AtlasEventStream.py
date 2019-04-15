# Event stream from ATLAS
from clientlib.EventStream import EventStream
from xAODlib.atlas_xaod_executor import atlas_xaod_executor
from xAODlib.util_scope import top_level_scope
import cpplib.cpp_representation as crep
import ast
import xAODlib.statement as statement

class Atlas_xAOD_File_Type:
    def __init__(self):
        pass

class AtlasXAODFileStream(ast.AST):
    r"""
    An AST node that represents the event source.
    """

    def __init__(self, ds_url):
        self.dataset_url = ds_url
        # Set a rep for ourselves, but it should never be directly used. We are the top level sequence.
        iterator = crep.cpp_value("bogus-do-not-use", top_level_scope(), Atlas_xAOD_File_Type())
        self.rep = crep.cpp_sequence(iterator, iterator)

    def get_executor(self):
        return atlas_xaod_executor(self.dataset_url)


class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """

    def __init__(self, evt_stream):
        EventStream.__init__(self, AtlasXAODFileStream(evt_stream._url))
