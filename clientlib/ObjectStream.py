# A stream of some object
import clientlib.query_ast as query_ast
from clientlib.query_result_asts import resultTTree, resultPandasDF, resultAwkwardArray
from clientlib.find_LINQ_operators import parse_ast
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
        return ObjectStream(query_ast.SelectMany(self._ast, parse_ast(func)))

    def Select(self, f):
        r"""
        User wants to transform a single object at a time in this stream.

        f - selection function
        """
        return ObjectStream(query_ast.Select(self._ast, parse_ast(f)))

    def Where(self, filter_lambda):
        r'''
        User wants to filter the sequence at the top level.
        '''
        return ObjectStream(query_ast.Where(self._ast, parse_ast(filter_lambda)))

    def AsPandasDF(self, columns=[]):
        r"""
        Return a pandas dataframe. We do this by running the conversion.

        columns - Array of names of the columns. Will default to "col0", "call1", etc.
        """

        # We do this by first generating a simple ROOT file, then loading it into a dataframe with
        # uproot.
        return ObjectStream(resultPandasDF(self._ast, columns))

    def AsROOTFile(self, columns=[]):
        r"""
        Terminal - take the AST and return a root file.

        columns - Array of names of the columns
        """
        return ObjectStream(resultTTree(self._ast, columns))

    def AsAwkwardArray(self, columns=[]):
        r'''
        Terminal - take the AST and return a root file.

        columns - Array of names of the columns
        '''
        return ObjectStream(resultAwkwardArray(self._ast, columns))

    def value(self):
        r"""
        Trigger the evaluation of the AST.
        """
        # Find the executor
        exe_finder = find_executor()
        exe_finder.visit(self._ast)
        if len(exe_finder.executors) != 1:
            raise BaseException(
                "Unable to find a single, unique, executor for expression (found " + str(len(exe_finder.executors)) + ").")
        exe = exe_finder.executors[0]

        # Apply any local transformations required.
        ast = exe.apply_ast_transformations(self._ast)

        # Now, find the executor and send it the AST
        return exe.evaluate(ast)


class find_executor(ast.NodeVisitor):
    def __init__(self):
        self.executors = []

    def generic_visit(self, node):
        if hasattr(node, "get_executor"):
            self.executors += [node.get_executor()]
        ast.NodeVisitor.generic_visit(self, node)
