# Event stream from ATLAS
from clientlib.EventStream import EventStream
from atlaslib.atlas_xaod_executor import atlas_xaod_executor
from clientlib.query_ast import base_ast


class atlas_file_event_stream_ast (base_ast):
    r"""
    An AST node that represents the event source.
    """
    def __init__ (self, ds_url):
        base_ast.__init__(self, None)
        self._ds = ds_url

    def get_executor(self):
        return atlas_xaod_executor(self._ds)

    def visit_ast(self, visitor):
        visitor.visit_atlas_file_event_stream_ast(self)

class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """
    def __init__(self, evt_stream):
        EventStream.__init__(self, atlas_file_event_stream_ast(evt_stream._url))
