# Code to help specify and work with datasets on the client end.
from xAODlib.AtlasEventStream import AtlasEventStream

# Bring in all the machinery to process xAOD files. This adds
# extra stuff to the processing engine to special case things.
import xAODlib.Jets
import xAODlib.EventCollections

class EventDataSet:
    def __init__(self, url):
        self._url = url

    def AsATLASEvents(self):
        r"""
        Returns a stream of events that knows it will have to run in an ATLAS environment.

        This should be an extension function, not on the EventDataSet which should be "neutral".
        """
        return AtlasEventStream(self)
