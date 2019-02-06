# Event stream from ATLAS
from clientlib.EventStream import EventStream


class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """
    def __init__(self, ds):
        EventStream.__init__(self, ds)
