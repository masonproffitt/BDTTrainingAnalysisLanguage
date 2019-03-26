# Various node visitors to clean up nested function calls of various types.
import ast
from clientlib.query_ast import Select, Where, SelectMany
from clientlib.ast_util import lambda_body, lambda_body_replace, lambda_wrap, lambda_unwrap, lambda_call, lambda_build

argument_var_counter = 0
def arg_name():
    'Return a unique name that can be used as an argument'
    global argument_var_counter
    n = 'arg_{0}'.format(argument_var_counter)
    argument_var_counter += 1
    return n

def convolute(ast_g, ast_f):
    'Return an AST that represents g(f(args))'
    #TODO: fix up the ast.Calls to use lambda_call if possible

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

    # TODO: Rewrite with lambda_build
    args = ast.arguments(args=[ast.arg(arg=x)])
    call_g_lambda = ast.Lambda(args=args, body=call_g)

    # Build a new call to nest the functions
    return lambda_wrap(call_g_lambda)

class simplify_chained_calls(ast.NodeTransformer):
    '''
    In order to cleanly evaluate things like tuples (which should not show up at the back end),
    we must move around various functions, evaluate others, etc., where we can. This AST transformer
    does that work.
    '''

    def __init__(self):
        self._arg_dict = {}

    def visit_Select_of_Select(self, parent, selection):
        r'''
        seq.Select(x: f(x)).Select(y: g(y))
        => Select(Select(seq, x: f(x)), y: g(y))
        is turned into
        seq.Select(x: g(f(x)))
        => Select(seq, x: g(f(x)))
        '''
        func_g = selection
        func_f = parent.selection

        # Convolute the two functions
        # TODO: should this be generic of just visit?
        new_selection = self.generic_visit(convolute(func_g, func_f))

        # And return the parent select with the new selection function
        return Select(parent.source, new_selection)

    def visit_Select_of_SelectMany(self, parent, selection):
        r'''
        seq.SelectMany(x: f(x)).Select(y: g(y))
        => Select(SelectMany(seq, x: f(x)), y: g(y))
        is turned into
        seq.SelectMany(x: f(x).Select(y: g(y)))
        => SelectMany(seq, x: Select(f(x), y: g(y)))
        '''
        func_g = selection
        func_f = parent.selection

        return self.visit(SelectMany(parent.source, lambda_body_replace(func_f, Select(lambda_body(func_f), func_g))))

    def visit_Select(self, node):
        r'''
        Transformation #1:
        seq.Select(x: f(x)).Select(y: g(y))
        => Select(Select(seq, x: f(x)), y: g(y))
        is turned into
        seq.Select(x: g(f(x)))
        => Select(seq, x: g(f(x)))

        Transformation #2:
        seq.SelectMany(x: f(x)).Select(y: g(y))
        => Select(SelectMany(seq, x: f(x)), y: g(y))
        is turned into
        seq.SelectMany(x: f(x).Select(y: g(y)))
        => SelectMany(seq, x: Select(f(x), y: g(y)))

        Transformation #3:
        seq.Where(x: f(x)).Select(y: g(y))
        => Select(Where(seq, x: f(x), y: g(y))
        is not altered.
        '''

        parent_select = self.visit(node.source)
        if type(parent_select) is Select:
            return self.visit_Select_of_Select(parent_select, node.selection)
        elif type(parent_select) is SelectMany:
            return self.visit_Select_of_SelectMany(parent_select, node.selection)
        else:
            return Select(parent_select, self.visit(node.selection))

    def visit_SelectMany_of_Select(self, parent, selection):
        '''
        seq.Select(x: f(x)).SelectMany(y: g(y))
        => SelectMany(Select(seq, x: f(x)), y:g(y))
        is turned into
        seq.SelectMany(x: g(f(x)))
        => SelectMany(seq, x: g(f(x)))
        '''
        func_g = selection
        func_f = parent.selection
        seq = parent.source

        new_selection = self.generic_visit(convolute(func_g, func_f))
        return self.visit(SelectMany(seq, new_selection))
    
    def visit_SelectMany_of_SelectMany(self, parent, selection):
        '''
        Transformation #1:
        seq.SelectMany(x: f(x)).SelectMany(y: f(y))
        => SelectMany(SelectMany(seq, x: f(x)), y: f(y))
        is turned into:
        seq.SelectMany(x: f(x).SelectMany(y: f(y)))
        => SelectMany(seq, x: SelectMany(f(x), y: f(y)))
        '''
        raise BaseException('untested')
        func_g = selection
        func_f = parent.selection

        return self.visit(SelectMany(parent.source, lambda_body_replace(func_f, SelectMany(lambda_body(func_f), func_g))))

    def visit_SelectMany(self, node):
        r'''
        Transformation #1:
        seq.SelectMany(x: f(x)).SelectMany(y: f(y))
        => SelectMany(SelectMany(seq, x: f(x)), y: f(y))
        is turned into:
        seq.SelectMany(x: f(x).SelectMany(y: f(y)))
        => SelectMany(seq, x: SelectMany(f(x), y: f(y)))

        Transformation #2:
        seq.Select(x: f(x)).SelectMany(y: g(y))
        => SelectMany(Select(seq, x: f(x)), y:g(y))
        is turned into
        seq.SelectMany(x: g(f(x)))
        => SelectMany(seq, x: g(f(x)))

        Transformation #3:
        seq.Where(x: f(x)).SelectMany(y: g(y))
        '''
        parent_select = self.visit(node.source)
        if type(parent_select) is SelectMany:
            return self.visit_SelectMany_of_SelectMany(parent_select, node.selection)
        elif type(parent_select) is Select:
            return self.visit_SelectMany_of_Select(parent_select, node.selection)
        else:
            return SelectMany(parent_select, self.visit(node.selection))

    def visit_Where_of_Where(self, parent, filter):
        '''
        seq.Where(x: f(x)).Where(x: g(x))
        => Where(Where(seq, x: f(x)), y: g(y))
        is turned into
        seq.Where(x: f(x) and g(y))
        => Where(seq, x: f(x) and g(y))
        '''
        func_f = parent.filter
        func_g = filter

        arg = arg_name()
        return self.visit(Where(parent.source, lambda_build(arg, ast.BoolOp(ast.And, [lambda_call(arg, func_f), lambda_call(arg, func_g)]))))

    def visit_Where_of_Select(self, parent, filter):
        '''
        seq.Select(x: f(x)).Where(y: g(y))
        => Where(Select(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.Where(x: g(f(x))).Select(x: f(x))
        => Select(Where(seq, x: g(f(x)), f(x))
        '''
        func_f = parent.selection
        func_g = filter
        seq = parent.source

        w = Where(seq, self.visit(convolute(func_g, func_f)))
        s = Select(w, func_f)

        # Recursively visit this mess to see if the Where needs to move further up.
        return self.visit(s)

    def visit_Where_of_SelectMany(self, parent, filter):
        '''
        seq.SelectMany(x: f(x)).Where(y: g(y))
        => Where(SelectMany(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.SelectMany(x: f(x).Where(y: g(y)))
        => SelectMany(seq, x: Where(f(x), g(y)))
        '''
        raise BaseException('untested')
        func_f = parent.selection
        func_g = filter
        seq = parent.source

        return self.visit(SelectMany(seq, lambda_body_replace(func_f, Where(lambda_body(func_f), func_g))))

    def visit_Where(self, node):
        r'''
        Transformation #1:
        seq.Where(x: f(x)).Where(x: g(x))
        => Where(Where(seq, x: f(x)), y: g(y))
        is turned into
        seq.Where(x: f(x) and g(y))
        => Where(seq, x: f(x) and g(y))

        Transformation #2:
        seq.Select(x: f(x)).Where(y: g(y))
        => Where(Select(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.Where(x: g(f(x))).Select(x: f(x))
        => Select(Where(seq, x: g(f(x)), f(x))
        
        Transformation #3:
        seq.SelectMany(x: f(x)).Where(y: g(y))
        => Where(SelectMany(seq, x: f(x)), y: g(y))
        Is turned into:
        seq.SelectMany(x: f(x).Where(y: g(y)))
        => SelectMany(seq, x: Where(f(x), g(y)))
        '''
        parent_where = self.visit(node.source)
        if type(parent_where) is Where:
            return self.visit_Where_of_Where(parent_where, node.filter)
        elif type(parent_where) is Select:
            return self.visit_Where_of_Select(parent_where, node.filter)
        elif type(parent_where) is SelectMany:
            return self.visit_Where_of_SelectMany(parent_where, node.filter)
        else:
            return Where(parent_where, self.visit(node.filter))
    
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