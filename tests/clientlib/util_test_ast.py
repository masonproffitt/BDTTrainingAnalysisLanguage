# Some helper routines
from clientlib.call_stack import argument_stack, stack_frame
import ast
import copy

class normalize_ast(ast.NodeTransformer):
    '''
    The AST's can have the same symantec meaning, but not the same text, so the string compare that happens as part of these tests fail. The code
    here's job is to make the ast produced by the local code look like the python code.
    '''
    def __init__ (self):
        self._arg_index = 0
        self._arg_stack = argument_stack()

    def new_arg(self):
        'Generate a new argument, in a nice order'
        old_arg = self._arg_index
        self._arg_index += 1
        return "t_arg_{0}".format(old_arg)

    def start_visit(self, node):
        return self.visit(copy.deepcopy(node))

    def visit_Lambda(self, node):
        'Arguments need a uniform naming'
        a_mapping = [(a.arg, self.new_arg()) for a in node.args.args]

        # Remap everything that is inside this guy
        with stack_frame(self._arg_stack):
            for m in a_mapping:
                self._arg_stack.define_name(m[0],m[1])
            body = self.visit(node.body)

        # Rebuild the lambda guy
        args = [ast.arg(arg=m[1]) for m in a_mapping]
        return ast.Lambda(args=args, body=body)

    def visit_Name(self, node):
        return ast.Name(self._arg_stack.lookup_name(node.id))
