from pythonarraylib.python_node_transformer import python_node_transformer

import ast

class python_array_ast_visitor(ast.NodeVisitor):
    def __init__(self):
        self._id_scopes = {}

    def visit(self, node):
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.visit(self, node)

    def generic_visit(self, node):
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.generic_visit(self, node)

    def get_rep(self, node):
        if node is None:
            return ''
        if not hasattr(node, 'rep'):
            self.visit(node)
        return node.rep

    def visit_Num(self, node):
        node.rep = repr(node.n)

    def visit_Str(self, node):
        node.rep = repr(node.s)

    def visit_List(self, node):
        node.rep = '[' + ', '.join(self.get_rep(element) for element in node.elts) + ']'

    def visit_Tuple(self, node):
        node.rep = '(' + ', '.join(self.get_rep(element) for element in node.elts) + ',)'

    def visit_Dict(self, node):
        node.rep = '{' + ', '.join(self.get_rep(key) + ': ' + self.get_rep(value) for key, value in zip(node.keys, node.values)) + '}'

    def resolve_id(self, id):
        if id in self._id_scopes or id in globals:
            return id
        else:
            raise NameError('Unknown id: ' + id)

    def visit_Name(self, node):
        node.rep = self.resolve_id(node.id)

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.UAdd):
            operator_rep = '+'
        elif isinstance(node.op, ast.USub):
            operator_rep = '-'
        elif isinstance(node.op, ast.Not):
            operator_rep = 'not '
        elif isinstance(node.op, ast.Invert):
            operator_rep = '~'
        else:
            raise SyntaxError('Unimplemented unary operation: ' + node.op)
        operand_rep = self.get_rep(node.operand)
        node.rep = '(' + operator_rep + operand_rep + ')'

    def visit_BinOp(self, node):
        left_rep = self.get_rep(node.left)
        if isinstance(node.op, ast.Add):
            operator_rep = '+'
        elif isinstance(node.op, ast.Sub):
            operator_rep = '-'
        elif isinstance(node.op, ast.Mult):
            operator_rep = '*'
        elif isinstance(node.op, ast.Div):
            operator_rep = '/'
        elif isinstance(node.op, ast.FloorDiv):
            operator_rep = '//'
        elif isinstance(node.op, ast.Mod):
            operator_rep = '%'
        elif isinstance(node.op, ast.Pow):
            operator_rep = '**'
        elif isinstance(node.op, ast.LShift):
            operator_rep = '<<'
        elif isinstance(node.op, ast.RShift):
            operator_rep = '>>'
        elif isinstance(node.op, ast.BitOr):
            operator_rep = '|'
        elif isinstance(node.op, ast.BitXor):
            operator_rep = '^'
        elif isinstance(node.op, ast.BitAnd):
            operator_rep = '&'
        else:
            raise SyntaxError('Unimplemented binary operation: ' + node.op)
        right_rep = self.get_rep(node.right)
        node.rep = '(' + left_rep + ' ' + operator_rep +  ' ' + right_rep + ')'

    def visit_BoolOp(self, node):
        if isinstance(node.op, ast.And):
            operator_rep = 'and'
        elif isinstance(node.op, ast.Or):
            operator_rep = 'or'
        else:
            raise SyntaxError('Unimplemented boolean operation: ' + node.op)
        node.rep = '(' + (' ' + operator_rep + ' ').join(self.get_rep(value) for value in node.values) + ')'

    @staticmethod
    def get_comparison_operator_rep(operator):
        if isinstance(operator, ast.Eq):
            return '=='
        elif isinstance(operator, ast.NotEq):
            return '!='
        elif isinstance(operator, ast.Lt):
            return '<'
        elif isinstance(operator, ast.LtE):
            return '<='
        elif isinstance(operator, ast.Gt):
            return '>'
        elif isinstance(operator, ast.GtE):
            return '>='
        elif isinstance(operator, ast.Is):
            return 'is'
        elif isinstance(operator, ast.IsNot):
            return 'is not'
        elif isinstance(operator, ast.In):
            return 'in'
        elif isinstance(operator, ast.NotIn):
            return 'not in'
        else:
            raise SyntaxError('Unimplemented comparison operation: ' + operator)

    def visit_Compare(self, node):
        left_rep = self.get_rep(node.left)
        node.rep = '(' + left_rep
        for operator, comparator in zip(node.ops, node.comparators):
            operator_rep = self.get_comparison_operator_rep(operator)
            comparator_rep = self.get_rep(comparator)
            node.rep += ' ' + operator_rep + ' ' + comparator_rep
        node.rep += ')'

    def visit_Index(self, node):
        node.rep = self.get_rep(node.value)

    def visit_Slice(self, node):
        lower_rep = self.get_rep(node.lower)
        upper_rep = self.get_rep(node.upper)
        node.rep = lower_rep + ':' + upper_rep
        step_rep = self.get_rep(node.step)
        if step_rep != '':
            node.rep += ':' + step_rep

    def visit_ExtSlice(self, node):
        node.rep = ', '.join(self.get_rep(dimension) for dimension in node.dims)

    def visit_Subscript(self, node):
        value_rep = self.get_rep(node.value)
        slice_rep = self.get_rep(node.slice)
        node.rep = value_rep + '[' + slice_rep + ']'

    def visit_Attribute(self, node):
        value_rep = self.get_rep(node.value)
        node.rep = '(' + value_rep + '.' + node.attr + ' if hasattr(' + value_rep + ", '" + node.attr + "') else " + value_rep + "['" + node.attr + "'])"

    def visit_Lambda(self, node):
        arg_strs = [arg_node.arg for arg_node in node.args.args]
        args_rep = ', '.join(arg_strs)
        for arg_str in arg_strs:
            if arg_str in self._id_scopes:
                self._id_scopes[arg_str] += 1
            else:
                self._id_scopes[arg_str] = 1
        body_rep = self.get_rep(node.body)
        node.rep = '(lambda ' + args_rep + ': ' + body_rep + ')'
        for arg_str in arg_strs:
            self._id_scopes[arg_str] -= 1
            if self._id_scopes[arg_str] == 0:
                del self._id_scopes[arg_str]

    def visit_Call(self, node):
        func_rep = self.get_rep(node.func)
        args_rep = ', '.join(self.get_rep(arg) for arg in node.args)
        node.rep = func_rep + '(' + args_rep + ')'

    def visit_Select(self, node):
        call_node = ast.Call(node.selection, [node.source])
        node.rep = self.get_rep(call_node)

    #def visit_SelectMany(self, node):
    #    self.visit_Select(node)
    #    node.rep += '.flatten()'

    #def visit_Where(self, node):
    #    if isinstance(node.filter, ast.Lambda):
    #        lambda_func = node.filter
    #    elif isinstance(node.filter, ast.Module):
    #        lambda_func = node.filter.body[0].value
    #    else:
    #        raise BaseException('unimplemented where filter: ' + node.filter)
    #    c = ast.Call(func=lambda_func, args=[node.source])
    #    node.rep = self.get_rep(node.source) + '[' + self.get_rep(c) + ']'

    #def visit_Aggregate(self, node):
    #    if len(node.args) == 2:
    #        if type(node.args[0]) is ast.Lambda:
    #            raise BaseException('not really sure how this kind of aggregate works...')
    #        else:
    #            init_value = node.args[0]
    #            agg_lambda = node.args[1]
    #    else:
    #        raise BaseException('not really sure how this kind of aggregate works...')
    #    node.rep = 'for ' + ' in ' + self.get_rep(node.func.value) + ':\n'
    #    node.rep += '    '

class python_array_executor:
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source

    def apply_ast_transformations(self, tree):
        tree = python_node_transformer().visit(tree)
        return tree
