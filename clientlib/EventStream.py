# A stream of events.
from clientlib.ObjectStream import ObjectStream

class EventStream(ObjectStream):
    def __init__(self, ds):
        r"""
        Keep a tag on the actual event dataset we are representing!
        """
        ObjectStream.__init__(self, None)
        self._ds = ds

    def get_executor(self):
        r"""
        Return the executor for this stream
        """
        raise BaseException("Event streams must have an associated executor")