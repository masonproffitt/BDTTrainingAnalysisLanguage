# Contains AST elements for the query part of an expression

class base_ast:
    r"""
    Base class for ast to provide some useful common tools
    """
    
    def __init__(self, source_ast):
        self._source = source_ast

    def get_executor (self):
        r"""
        Return the executor. This should climb the chain until it hits an ast that
        knows how to run. Usually this is the data file (the ROOT file?)
        """
        if self._source:
            return self._source.get_executor()
        else:
            raise BaseException("internal bug: get_executor should not be called with a null source.")

class select_many_ast(base_ast):
    r"""
    AST node for select many. Incoming type is a collection
    """

    def __init__(self, source_ast, selection_function):
        r"""
        source_ast - an AST that represents a collection
        """
        base_ast.__init__(self, source_ast)
        self._selection_function = selection_function

class select_ast (base_ast):
    r"""
    AST node for select. Transforms the input to the output.
    """

    def __init__(self, source_ast, select_function):
        base_ast.__init__(self, source_ast)
        self._selection_function = select_function

