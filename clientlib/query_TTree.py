# Collected code to emit a ROOT file containing a TTree.
from clientlib.query_ast import base_ast

class ttree_terminal_ast (base_ast):
    def __init__ (self, source_ast, column_names, output_filename):
        base_ast.__init__(self, source_ast)
        self._column_names = column_names
        self._filename = output_filename

    def visit_ast (self, visitor):
        visitor.visit_ttree_terminal_ast(self)