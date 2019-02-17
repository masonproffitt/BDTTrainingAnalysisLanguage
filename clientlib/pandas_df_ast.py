# AST for a creating a pandas df from a source.
import ast

class CreatePandasDF(ast.AST):
    r'''
    AST representing the creating of a Pandas DF from some source.
    Note: not quite sure how this fits in as it requires a ROOT file first, and not an iterator (at the moment). Need
    to re-do the implementation when we have data sources that are flat root files and pandas DF's.
    '''
    def __init__ (self, source):
        r'''
        Create the AST that converts the source into a dataframe
        '''
        self.source = source
        self._fields = ('source',)
