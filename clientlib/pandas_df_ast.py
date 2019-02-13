# Code related to converting a root file into a pandas DF
from clientlib.query_ast import base_ast

class panads_df_ast (base_ast):
    def __init__ (self, source_ast):
        base_ast.__init__(self, source_ast)

    def visit_ast (self, visitor):
        visitor.visit_panads_df_ast(self)
