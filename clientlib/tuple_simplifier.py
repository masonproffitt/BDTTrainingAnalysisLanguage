# Simplify tuple access.
import ast

class remove_tuple_subscripts(ast.NodeTransformer):
    r'''
    Turns (e1, e2, e3)[0] into just e1.
    '''

    def visit_Subscript(self, subnode):
        pass