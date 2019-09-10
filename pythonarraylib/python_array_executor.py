from pythonarraylib.python_array_node_transformer import python_array_node_transformer

class python_array_executor:
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source

    def apply_ast_transformations(self, tree):
        return python_array_node_transformer().visit(tree)
