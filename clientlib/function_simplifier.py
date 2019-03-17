# Various node visitors to clean up nested function calls of various types.
import ast
from clientlib.query_ast import Select, Where
from clientlib.ast_util import lambda_body, replace_lambda_body, wrap_lambda

argument_var_counter = 0
def arg_name():
    'Return a unique name that can be used as an argument'
    global argument_var_counter
    n = 'arg_{0}'.format(argument_var_counter)
    argument_var_counter += 1
    return n

def convolute(ast_g, ast_f):
    'Return an AST that represents g(f(args))'

    # Sanity checks. For example, g can have only one input argument (e.g. f's result)
    if (type(ast_g.body[0]) is not ast.Expr) or (type(ast_f.body[0]) is not ast.Expr):
        raise BaseException("Only lambdas in Selects!")
    if (type(ast_g.body[0].value) is not ast.Lambda) or (type(ast_f.body[0].value) is not ast.Lambda):
        raise BaseException("Only lambdas in Selects!")
    
    # Combine the lambdas into a single call by calling g with f as an argument
    l_g = ast_g.body[0].value
    l_f = ast_f.body[0].value

    x = arg_name()
    f_arg = ast.Name(x, ast.Load())
    call_g = ast.Call(l_g, [ast.Call(l_f, [f_arg], [])], [])

    args = ast.arguments(args=[ast.arg(arg=x)])
    call_g_lambda = ast.Lambda(args=args, body=call_g)

    # Build a new call to nest the functions
    return wrap_lambda(call_g_lambda)

class simplify_chained_calls(ast.NodeTransformer):
    '''
    something.Select(x: f(x)).Select(y: g(y))
    is turned into
    something.Select(x: g(f(x)))
    '''

    def __init__(self):
        self._arg_dict = {}

    def visit_Select(self, node):
        'Select call made - if this is a chained select call, then we can perhaps combine functions'
        parent_select = self.visit(node.source)
        # If we are a chained select, grab that select.
        if type(parent_select) is not Select:
            node.selection = self.visit(node.selection)
            return node

        # Select(x: f(x)).Select(y: g(y)) needs to be turned into Select(x: g(f(x))).
        func_g = node.selection
        func_f = parent_select.selection

        # Next the functions (they are in module syntax right now)
        parent_select.selection = self.generic_visit(convolute(func_g, func_f))

        # And return the parent select with the new selection function
        return parent_select

    def visit_SelectMany(self, node):
        'SelectMany call made, if this is chained to another select call, then we can combine functions'

        # If we are a chained select, grab that select.
        parent_select = self.visit(node.source)
        if type(parent_select) is Select:
            # Select(x: f(x)).SelectMany(y: g(y)) needs to be turned into SelectMany(x: g(f(x))).
            func_g = node.selection
            func_f = parent_select.selection

            # Replace our SelectMany selection with this update, and then
            # use the selects source for our own.
            node.selection = self.generic_visit(convolute(func_g, func_f))
            node.source = parent_select.source
        else:
            node.selection = self.visit(node.selection)

        # If the SM's selection function ends in a select.
        # SM(x: h(x).S(y: f(y))) ==> SM(x: h(x)).S(y: f(y))
        select_body = lambda_body(node.selection)
        if type(select_body) is Select:
            node.selection = replace_lambda_body(node.selection, select_body.source)
            node = Select(node, select_body.selection)

        # And return the parent select with the new selection function
        return node

    def visit_Where_after_select(self, parent_select, filter):
        '''Translate `.Select.Where` to `.Where.Select` '''

        # Unwind all the bits we are going to have to go after.
        s_source = parent_select.source
        s_func = parent_select.selection

        # Create the where ast
        w = Where(s_source, self.visit(convolute(filter, s_func)))

        # Nest it inside a new select
        s = Select(w, s_func)

        # Recursively visit this mess to see if the Where needs to move further up.
        return self.visit(s)

    def visit_Where(self, node):
        r'''
        We implement two translations here:
        
        1. `seq.Select(x: f(x)).Where(y: g(y))` => `seq.Where(x: g(f(x))).Select(x: f(x))` Of course
           this has to be repeatedly applied moving the Where as far up as possible.
        '''

        # Look for pattern 1 or pattern 2.
        parent_where = self.visit(node.source)
        if type(parent_where) is Select:
            return self.visit_Where_after_select(parent_where, node.filter)
        
        # Ok, nothing matched. Pass the parsing on down and return that.
        node.filter = self.visit(node.filter)
        return node
    
    def visit_Call(self, call_node):
        '''We are looking for cases where an argument is another function or expression.
        In that case, we want to try to get an evaluation of the argument, and replace it in the
        AST of this function. This only works of the function we are calling is a lambda.
        '''
        if type(call_node.func) is ast.Lambda:
            arg_asts = [self.visit(a) for a in call_node.args]
            for a_name, arg in zip(call_node.func.args.args, arg_asts):
                # TODO: These have to be removed correctly (deal with common arg names!)
                self._arg_dict[a_name.arg] = arg
            # Now, evaluate the expression, and then lift it.
            expr = self.visit(call_node.func.body)
            return expr
        else:
            call_node = self.generic_visit(call_node)
        return call_node

    def visit_Name(self, name_node):
        'Do lookup and see if we should translate or not.'
        if name_node.id in self._arg_dict:
            return self._arg_dict[name_node.id]
        return name_node