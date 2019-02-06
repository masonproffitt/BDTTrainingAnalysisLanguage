# A stream of events.

class EventStream:
    def __init__(self, ds):
        r"""
        Keep a tag on the actual event dataset we are representing!
        """
        self._ds = ds