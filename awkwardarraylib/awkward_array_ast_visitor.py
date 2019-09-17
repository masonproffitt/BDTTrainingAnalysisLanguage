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
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.selection.axis = node.axis + 1
        call_node = self.visit(ast.Call(node.selection, [node.source]))
        node.rep = self.get_rep(call_node)
        return node

    def visit_Count(self, node):
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.axis -= 1
        node.rep = self.get_rep(node.source) + '.count()'
        return node

    def visit_Min(self, node):
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.axis -= 1
        node.rep = self.get_rep(node.source) + '.min()'
        return node

    def visit_Max(self, node):
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.axis -= 1
        node.rep = self.get_rep(node.source) + '.max()'
        return node

    def visit_Sum(self, node):
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.axis -= 1
        node.rep = self.get_rep(node.source) + '.sum()'
        return node

    def visit_Average(self, node):
        if not hasattr(node, 'axis'):
            node.source = self.visit(node.source)
            node.axis = node.source.axis
        node.axis -= 1
        node.rep = self.get_rep(node.source) + '.mean()'
        return node
