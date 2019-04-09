from clientlib.query_ast import Where

import ast

class python_node_transformer(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.visit(node.func)
            for arg in node.args:
                self.visit(arg)
            if node.func.attr == "Count":
                new_call = ast.Call(func=ast.Name(id='len'), args=[node.func.value])
                return new_call
            elif node.func.attr == "Min":
                new_call = ast.Call(func=ast.Name(id='min'), args=[node.func.value])
                return new_call
            elif node.func.attr == "Max":
                new_call = ast.Call(func=ast.Name(id='max'), args=[node.func.value])
                return new_call
            elif node.func.attr == "Where":
                new_call = Where(source=node.func.value, filter_lambda=node.args[0])
                return new_call
            return node
        self.generic_visit(node)
        return node
