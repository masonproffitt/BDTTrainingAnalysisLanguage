# Collected code to emit a ROOT file containing a TTree.
from clientlib.query_ast import base_ast

class ttree_terminal_ast (base_ast):
    def __init__ (self, source_ast, column_names):
        base_ast.__init__(self, source_ast)
        self._column_names = column_names

    def visit_ast (self, visitor):
        visitor.visit_ttree_terminal_ast(self)

    def column_names (self):
        'Return a list of the column names'
        return self._column_names