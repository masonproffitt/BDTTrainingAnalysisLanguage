# AST and friends that denote a note that will emit a TTree.
import ast


class CreateTTreeFile(ast.AST):
    r'''
    An AST node that transforms a iterator into a TTree file.
    '''

    def __init__(self, source, column_names):
        r'''
        Initialize the CreateTTree AST node.

        source - The iterator containing the data that is to be written out to a TTree.
        column_names - Names of each column to be written out. Each is a string.
        '''
        self.source = source
        self.column_names = column_names
        self._fields = ('source',)
