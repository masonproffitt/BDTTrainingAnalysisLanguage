import ast

unary_op_dict = {ast.UAdd: '+',
                 ast.USub: '-',
                 ast.Not: 'not ',
                 ast.Invert: '~'}

bin_op_dict = {ast.Add: '+',
               ast.Sub: '-',
               ast.Mult: '*',
               ast.Div: '/',
               ast.FloorDiv: '//',
               ast.Mod: '%',
               ast.Pow: '**',
               ast.LShift: '<<',
               ast.RShift: '>>',
               ast.BitOr: '|',
               ast.BitXor: '^',
               ast.BitAnd: '&'}

bool_op_dict = {ast.And: 'and',
                ast.Or: 'or'}

compare_op_dict = {ast.Eq: '==',
                   ast.NotEq: '!=',
                   ast.Lt: '<',
                   ast.LtE: '<=',
                   ast.Gt: '>',
                   ast.GtE: '>=',
                   ast.Is: 'is',
                   ast.IsNot: 'is not',
                   ast.In: 'in',
                   ast.NotIn: 'not in'}

class python_array_ast_visitor(ast.NodeVisitor):
    def __init__(self):
        self._id_scopes = {}

    def visit(self, node):
        if hasattr(node, 'rep'):
            return node
        else:
            return ast.NodeVisitor.visit(self, node)

    def generic_visit(self, node):
        if hasattr(node, 'rep'):
            return node
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
        return node

    def visit_Str(self, node):
        node.rep = repr(node.s)
        return node

    def visit_List(self, node):
        node.rep = '[' + ', '.join(self.get_rep(element) for element in node.elts) + ']'
        return node

    def visit_Tuple(self, node):
        node.rep = '(' + ', '.join(self.get_rep(element) for element in node.elts) + ',)'
        return node

    def visit_Dict(self, node):
        node.rep = '{' + ', '.join(self.get_rep(key) + ': ' + self.get_rep(value) for key, value in zip(node.keys, node.values)) + '}'
        return node

    def get_globals():
        raise NotImplementedError("Pure virtual function")

    def resolve_id(self, id):
        if id in self._id_scopes or id in self.get_globals():
            return id
        else:
            raise NameError('Unknown id: ' + id)

    def visit_Name(self, node):
        node.rep = self.resolve_id(node.id)
        return node

    def visit_UnaryOp(self, node):
        if type(node.op) not in unary_op_dict:
            raise SyntaxError('Unimplemented unary operation: ' + node.op)
        operator_rep = unary_op_dict[type(node.op)]
        operand_rep = self.get_rep(node.operand)
        node.rep = '(' + operator_rep + operand_rep + ')'
        return node

    def visit_BinOp(self, node):
        left_rep = self.get_rep(node.left)
        if type(node.op) not in bin_op_dict:
            raise SyntaxError('Unimplemented binary operation: ' + node.op)
        operator_rep = bin_op_dict[type(node.op)]
        right_rep = self.get_rep(node.right)
        node.rep = '(' + left_rep + ' ' + operator_rep +  ' ' + right_rep + ')'
        return node

    def visit_BoolOp(self, node):
        if type(node.op) not in bool_op_dict:
            raise SyntaxError('Unimplemented boolean operation: ' + node.op)
        operator_rep = bool_op_dict[type(node.op)]
        node.rep = '(' + (' ' + operator_rep + ' ').join(self.get_rep(value) for value in node.values) + ')'
        return node

    def visit_Compare(self, node):
        left_rep = self.get_rep(node.left)
        node.rep = '(' + left_rep
        for operator, comparator in zip(node.ops, node.comparators):
            if type(operator) not in compare_op_dict:
                raise SyntaxError('Unimplemented comparison operation: ' + operator)
            operator_rep = compare_op_dict[type(operator)]
            comparator_rep = self.get_rep(comparator)
            node.rep += ' ' + operator_rep + ' ' + comparator_rep
        node.rep += ')'
        return node

    def visit_Index(self, node):
        node.rep = self.get_rep(node.value)
        return node

    def visit_Slice(self, node):
        lower_rep = self.get_rep(node.lower)
        upper_rep = self.get_rep(node.upper)
        node.rep = lower_rep + ':' + upper_rep
        step_rep = self.get_rep(node.step)
        if step_rep != '':
            node.rep += ':' + step_rep
        return node

    def visit_ExtSlice(self, node):
        node.rep = ', '.join(self.get_rep(dimension) for dimension in node.dims)
        return node

    def visit_Subscript(self, node):
        value_rep = self.get_rep(node.value)
        slice_rep = self.get_rep(node.slice)
        node.rep = value_rep + '[' + slice_rep + ']'
        return node

    def visit_Attribute(self, node):
        value_rep = self.get_rep(node.value)
        node.rep = '(' + value_rep + '.' + node.attr + ' if hasattr(' + value_rep + ", '" + node.attr + "') else " + value_rep + "['" + node.attr + "'])"
        return node

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
        return node

    def visit_Call(self, node):
        func_rep = self.get_rep(node.func)
        args_rep = ', '.join(self.get_rep(arg) for arg in node.args)
        node.rep = func_rep + '(' + args_rep + ')'
        return node

    def visit_Select(self, node):
        raise NotImplementedError("Pure virtual function")

    def visit_SelectMany(self, node):
        call_node = self.visit(ast.Call(ast.Attribute(node, 'flatten')))
        node.rep = self.get_rep(call_node)
        return node

    def visit_Where(self, node):
        if type(node.filter) is not ast.Lambda:
            raise TypeError('Argument to Where() must be a lambda function, found ' + node.filter)
        if len(node.filter.args.args) != 1:
            raise TypeError('Lambda function in Where() must have exactly one argument, found ' + len(node.filter.args.args))
        node.filter.body = ast.Subscript(ast.Name(node.filter.args.args[0].arg), ast.Index(node.filter.body))
        call_node = self.visit(ast.Call(node.filter, [node.source]))
        node.rep = self.get_rep(call_node)
        return node
