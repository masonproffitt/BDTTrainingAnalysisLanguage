from clientlib.ObjectStream import ObjectStream

class ArrayStream(ObjectStream):
    def __init__(self, dataset_ast):
        ObjectStream.__init__(self, dataset_ast)
