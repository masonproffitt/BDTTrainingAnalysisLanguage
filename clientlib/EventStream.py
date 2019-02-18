# A stream of events.
from clientlib.ObjectStream import ObjectStream


class EventStream(ObjectStream):
    def __init__(self, ds_ast):
        r"""
        Keep a tag on the actual event dataset we are representing!

        ds_ast is the source ast that contains the input dataset to be
        processed.
        """
        ObjectStream.__init__(self, ds_ast)
