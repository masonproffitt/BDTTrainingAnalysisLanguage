# Code to help specify and work with datasets on the client end.
from atlaslib.AtlasEventStream import AtlasEventStream

class EventDataSet:
    def __init__ (self, args):
        self._url = args[0]

    def AsATLASEvents(self):
        r"""
        Returns a stream of events that knows it will have to run in an ATLAS environment.
        
        This should be an extension function, not on the EventDataSet which should be "neutral".
        """
        return AtlasEventStream(self)