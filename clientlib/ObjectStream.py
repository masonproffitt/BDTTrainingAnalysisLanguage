# A stream of some object
import clientlib.query_ast as query_ast
import clientlib.query_TTree as query_TTree
import clientlib.pandas_df_ast as pandas_df_ast
import ast


class ObjectStream:
    def __init__(self, ast):
        r"""
        Each node in an AST knows about its parent, so you can track all the way back.
        """
        self._ast = ast
        pass

    def SelectMany(self, func):
        r"""
        The user wants to unroll a collection. This func needs to:
        1. Figure out what needs to be done to get at the collection
        2. Return a stream of new objects.

        func - a string that can be compiled to a python AST.
        """
        return ObjectStream(query_ast.SelectMany(self._ast, ast.parse(func)))

    def Select(self, f):
        r"""
        User wants to transform a single object at a time in this stream.

        f - selection function
        """
        return ObjectStream(query_ast.Select(self._ast, ast.parse(f)))

    def AsPandasDF(self, columns=[]):
        r"""
        Return a pandas dataframe. We do this by running the conversion.

        columns - Array of names of the columns. Will default to "col0", "call1", etc.
        """

        # We do this by first generating a simple ROOT file, then loading it into a dataframe with
        # uproot.
        return self.AsROOTFile(columns=columns).AsPandasDFFromROOTFile()

    def AsROOTFile(self, columns=[]):
        r"""
        Terminal - take the AST and return a root file.

        columns - Array of names of the columns
        """
        # Fix up the number of columns
        if len(columns) == 0:
            columns = ['col0']

        return ObjectStream(query_TTree.CreateTTreeFile(self._ast, columns))

    def AsPandasDFFromROOTFile(self):
        r"""
        Return a pandas df frame from the root file.
        """

        return ObjectStream(pandas_df_ast.CreatePandasDF(self._ast))

    def value(self):
        r"""
        Trigger the evaluation of the AST.
        """

        exe = find_executor()
        exe.visit(self._ast)
        if len(exe.executors) != 1:
            raise BaseException(
                "Unable to find a single, unique, executor for expression (found " + str(len(exe.executors)) + ").")
        return exe.executors[0].evaluate(self._ast)


class find_executor(ast.NodeVisitor):
    def __init__(self):
        self.executors = []

    def generic_visit(self, node):
        if hasattr(node, "get_executor"):
            self.executors += [node.get_executor()]
        ast.NodeVisitor.generic_visit(self, node)
