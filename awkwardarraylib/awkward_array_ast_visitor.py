from pythonarraylib.python_array_ast_visitor import python_array_ast_visitor

import awkward

import ast
import os

class awkward_array_ast_visitor(python_array_ast_visitor):
    def get_globals(self):
        return globals()

    def visit_Select(self, node):
        if type(node.selection) is not ast.Lambda:
            raise TypeError('Argument to Select() must be a lambda function, found ' + node.selection)
        if len(node.selection.args.args) != 1:
            raise TypeError('Lambda function in Select() must have exactly one argument, found ' + len(node.selection.args.args))
        if type(node.selection.body) in (ast.List, ast.Tuple):
            node.selection.body = ast.Call(ast.Attribute(ast.Name('awkward'), 'Table'), node.selection.body.elts)
        if type(node.selection.body) is ast.Dict:
            node.selection.body = ast.Call(ast.Attribute(ast.Name('awkward'), 'Table'), [node.selection.body])
        call_node = self.visit(ast.Call(node.selection, [node.source]))
        node.rep = self.get_rep(call_node)
        return node
