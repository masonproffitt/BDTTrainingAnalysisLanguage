# Some ast utils
import ast
from sys import stdout

class pretty_print_visitor(ast.NodeVisitor):
    def __init__(self, stream):
        self._s = stream
        self._indent = 1

    def print_fields (self, node):
        'Handle different types of fields'
        if isinstance(node, list):
            self._s.write('    '*self._indent + '[\n')
            self._indent += 1
            for f in node:
                self.print_fields(f)
                self._s.write(',\n')
            self._indent -= 1
            self._s.write('    '*self._indent + ']\n')
        elif isinstance(node, ast.AST):
            first = True
            for field, value in ast.iter_fields(node):
                if not first:
                    self._s.write(',\n')
                first = False

                self._s.write('    '*self._indent + field + "=")
                self._indent += 1
                self.visit(value)
                self._indent -= 1
        elif node is None:
            pass
        else:
            self._s.write(str(node))

    def count_fields(self, node):
        'How many fields are there down a level?'
        if isinstance(node, list):
            return len(node)
        elif isinstance(node, ast.AST):
            return len(list(ast.iter_fields(node)))
        elif node is None:
            return 0
        else:
            return 0

    def generic_visit(self, node):
        self._s.write(node.__class__.__name__)
        self._s.write('(')
        if self.count_fields(node) > 0:
            self._s.write('\n')
            self.print_fields (node)
            self._s.write('    '*self._indent)
        self._s.write(')')

    def visit_Num(self, node):
        self._s.write('Num(n={0})'.format(node.n))

    def visit_str(self, node):
        self._s.write('"{0}"'.format(node))

    def visit_Name(self, node):
        self._s.write('Name(id="{0}")'.format(node.id))

def pretty_print (ast):
    'Pretty print an ast'
    pretty_print_visitor(stdout).visit(ast)
    stdout.write("\n")

# Following are some tools to help with lambdas
def lambda_wrap(l):
    '''
    Given an AST lambda node, correctly wrap it in a module the way the python parser does.

    l: Must be an ast.Lambda node.

    Returns:
    
    m: a Module AST node with an Expr statement for the body, which holds the lambda.
    '''

    if type(l) is not ast.Lambda:
        raise BaseException('Attempt to wrap type {0} as a Lambda function, but it is not one!'.format(type(l)))

    return ast.Module(body=[ast.Expr(l)])

def lambda_args(l):
    'Return the arguments of a lambda'
    return lambda_unwrap(l).args

def lambda_unwrap(l):
    'Given an AST of a lambda node, return the lambda node. If it is burried in a module, then unwrap it'
    lb = l.body[0].value if type(l) is ast.Module else l
    if type(lb) is not ast.Lambda:
        raise BaseException('Attempt to get lambda expression body from {0}, which is not a lambda.'.format(type(l)))

    return lb

def lambda_body(l):
    '''
    Given an AST lambda node, get the expression it uses and return it. This just makes life easier,
    no real logic is occuring here.
    '''
    return lambda_unwrap(l).body

def lambda_call(args, l):
    '''
    Call a lambda with the named args.

    args: a single string or a list of strings
    l: The lambda we want to call. I can be wrapped in a module (or not).
    '''
    if type(args) is str:
        args = [args]
    named_args = [ast.Name(x, ast.Load()) for x in args]
    return ast.Call(lambda_unwrap(l), named_args, [])

def lambda_build(args, l_expr):
    '''
    Given a named argument(s), and an expression, build a lambda wrapped in a Module.

    args: the string names of the arguments to the lambda. May be a list or a single name
    l_expr: An AST node that is the body of the lambda.
    '''
    if type(args) is str:
        args = [args]
    ast_args = ast.arguments(args=[ast.arg(arg=x) for x in args])
    call_lambda = ast.Lambda(args=ast_args, body=l_expr)
    return lambda_wrap(call_lambda)

def lambda_body_replace(l, new_expr):
    '''
    Return a new lambda function that has new_expr as the body rather than the old one. Otherwise, everything is the same.

    l: A ast.Lambda or ast.Module that points to a lambda.
    new_expr: Expression that should replace this one.

    Returns:

    new_l: New lambda that looks just like the old one, other than the expression is new. If the old one was an ast.Module, so will this one be.
    '''
    lb = l.body[0].value if type(l) is ast.Module else l
    if type(lb) is not ast.Lambda:
        raise BaseException('Attempt to get lambda expression body from {0}, which is not a lambda.'.format(type(l)))

    new_l = ast.Lambda(lb.args, new_expr)
    return lambda_wrap(new_l) if type(l) is ast.Module else l

def lambda_assure(east, nargs=None):
    r'''
    Make sure the Python expression ast is a lambda call, and that it has the right number of args.

    east - python expression ast (module ast)
    nargs - number of args it is required to have. If None, no check is done.
    '''
    if not lambda_test(east, nargs):
        raise BaseException(
            'Expression AST is not a lambda function with the right number of arguments')

    return east


def lambda_test(east, nargs):
    r''' Test arguments
    TODO: Either fill this in or eliminate it.
    '''
    return True
