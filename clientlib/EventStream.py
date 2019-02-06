# A stream of events.
from clientlib.ObjectStream import ObjectStream

class EventStream(ObjectStream):
    def __init__(self, ds):
        r"""
        Keep a tag on the actual event dataset we are representing!
        """
        self._ds = ds
