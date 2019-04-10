# In an AST replace LINQ operations with the proper
# AST entries.
import clientlib.query_ast as query_ast
from clientlib.ast_util import lambda_unwrap
import ast


def parse_ast (ast_text):
    '''Parse a string as a LINQ ast
    
    NOTE: This must be called for every AST that the framework is converting from text.

    ast_text: String containing a lambda function

    returns:

    ast: The python AST representing the function, with Select, SelectMany, etc., properly converted
         to function call AST's.
    '''
    a = ast.parse(ast_text)
    return lambda_unwrap(replace_LINQ_operators().visit(a))

class replace_LINQ_operators(ast.NodeTransformer):
    r'''
    We are called on expressions that are parsed in-line, and when we see calls to things like Select, we replace them
    with the AST entries appropriate.

    ObjectStream has methods called Select and SelectMany. When they are called, they build up the AST tree. But they do that
    by creating Select and SelectMany, etc., ast nodes. When we parse a lambda passed as text, that does not happen. This
    NodeTransformer does that replacement in-place.
    '''

    def visit_Call(self, node):
        '''Look for LINQ type calls and make a replacement with the appropriate AST entry
        TODO: Make sure this is recursive properly!
        '''
        if type(node.func) is ast.Attribute:
            func_name =  node.func.attr
            if func_name == "Select":
                source = self.visit(node.func.value)
                selection = self.visit(node.args[0])
                return query_ast.Select(source, selection)
            elif func_name == "SelectMany":
                source = self.visit(node.func.value)
                selection = self.visit(node.args[0])
                return query_ast.SelectMany(source, selection)
            elif func_name == "Where":
                source = self.visit(node.func.value)
                filter = self.visit(node.args[0])
                return query_ast.Where(source, filter)
            elif func_name == "First":
                source = self.visit(node.func.value)
                return query_ast.First(source)
            else:
                return self.generic_visit(node)
        return node
