# Event stream from ATLAS
from clientlib.EventStream import EventStream
from atlaslib.atlas_xaod_executor import atlas_xaod_executor


class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """
    def __init__(self, ds):
        EventStream.__init__(self, ds)

    def get_executor(self):
        r"""
        Return the executor for this xAOD file from ATLAS
        """
        return atlas_xaod_executor()