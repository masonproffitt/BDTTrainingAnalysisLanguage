from pythonarraylib.python_node_transformer import python_node_transformer

import ast

class python_array_ast_visitor(ast.NodeVisitor):
    def __init__(self):
        self._var_dict = {}

    def generic_visit(self, node):
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.generic_visit(self, node)

    def visit(self, node):
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.visit(self, node)

    def get_rep(self, node):
        if not hasattr(node, 'rep'):
            self.visit(node)
        return node.rep

    def resolve_id(self, id):
        if id in self._var_dict:
            id = self._var_dict[id]
        if isinstance(id, ast.AST):
            id = self.get_rep(id)
        return id

    def visit_Num(self, node):
        node.rep = str(node.n)

    def visit_Str(self, node):
        node.rep = "r'" + node.s + "'"

    def visit_Tuple(self, node):
        #node.rep = '(' + ''.join(self.get_rep(e) + ', ' for e in node.elts) + ')'
        node.rep = '[' + ''.join(self.get_rep(e) + ', ' for e in node.elts) + ']'

    def visit_Subscript(self, node):
        node.rep = self.get_rep(node.value)
        if self.get_rep(node.value) == 'base_array':
            node.rep += '[:]'
        if node.rep[-2:] == ':]':
            node.rep = node.rep[:-1] + ','
        else:
            node.rep += '['
        node.rep += self.get_rep(node.slice.value) + ']'

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.UAdd):
            node.rep = '+'
        elif isinstance(node.op, ast.USub):
            node.rep = '-'
        elif isinstance(node.op, ast.Not):
            node.rep = '!'
        else:
            raise BaseException('unimplemented unary operation: ' + node.op)
        operand_rep = self.get_rep(node.operand)
        node.rep += operand_rep

    def visit_BinOp(self, node):
        left_rep = self.get_rep(node.left)
        node.rep = '(' + left_rep
        if isinstance(node.op, ast.Add):
            node.rep += ' + '
        elif isinstance(node.op, ast.Sub):
            node.rep += ' - '
        elif isinstance(node.op, ast.Mult):
            node.rep += ' * '
        elif isinstance(node.op, ast.Div):
            node.rep += ' / '
        else:
            raise BaseException('unimplemented binary operation: ' + node.op)
        right_rep = self.get_rep(node.right)
        node.rep += right_rep + ')'

    def visit_BoolOp(self, node):
        if len(node.values) != 2:
            raise BaseException('unimplemented boolean operation')
        left_rep = self.get_rep(node.values[0])
        node.rep = '(' + left_rep
        if isinstance(node.op, ast.And):
            node.rep += ' and '
        elif isinstance(node.op, ast.Or):
            node.rep += ' or '
        else:
            raise BaseException('unimplemented boolean operation: ' + node.op)
        right_rep = self.get_rep(node.values[1])
        node.rep += right_rep + ')'

    def visit_Compare(self, node):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise BaseException('unimplemented comparison operation')
        left_rep = self.get_rep(node.left)
        node.rep = '(' + left_rep
        operator = node.ops[0]
        if isinstance(operator, ast.Eq):
            node.rep += ' == '
        elif isinstance(operator, ast.NotEq):
            node.rep += ' != '
        elif isinstance(operator, ast.Lt):
            node.rep += ' < '
        elif isinstance(operator, ast.LtE):
            node.rep += ' <= '
        elif isinstance(operator, ast.Gt):
            node.rep += ' > '
        elif isinstance(operator, ast.GtE):
            node.rep += ' >= '
        else:
            raise BaseException('unimplemented comparison operation')
        right_rep = self.get_rep(node.comparators[0])
        node.rep += right_rep + ')'

    def visit_Name(self, node):
        node.rep = self.resolve_id(node.id)

    def visit_Attribute(self, node):
        calling_against = self.get_rep(node.value)
        attr_name = node.attr
        node.rep = calling_against + "['" + attr_name + "']"
        if calling_against == 'base_array':
            node.rep += '[:]'

    def visit_Lambda(self, node):
        for c_arg, l_arg in zip(node.args, node.func.args.args):
            self._var_dict[l_arg.arg] = c_arg

        node.rep = self.get_rep(node.func.body)

        for l_arg in node.func.args.args:
            del self._var_dict[l_arg.arg]

    def visit_Call(self, node):
        if isinstance(node.func, ast.Lambda):
            self.visit_Lambda(node)
        elif type(node.func) is ast.Compare:
            self.visit_Compare(node)
        elif isinstance(node.func, ast.Name):
            node.rep = 'awkward.fromiter('
            if node.func.id == 'len' and len(node.args) == 1:
                if isinstance(node.args[0], ast.Compare):
                    node.rep += '[len(object_with_length.nonzero()[0]) for object_with_length in ' + self.get_rep(node.args[0]) + ']'
                else:
                    node.rep += '[len(object_with_length) for object_with_length in ' + self.get_rep(node.args[0]) + ']'
            elif node.func.id == 'min' and len(node.args) == 1:
                node.rep += '[min(iterable) for iterable in ' + self.get_rep(node.args[0]) + ']'
            elif node.func.id == 'max' and len(node.args) == 1:
                node.rep += '[max(iterable) for iterable in ' + self.get_rep(node.args[0]) + ']'
            else:
                raise BaseException('unimplemented func call: ' + node.func.id)
            node.rep += ')'
        else:
            raise BaseException('unimplemented func call: ' + node.func)

    def visit_Select(self, node):
        c = ast.Call(node.selection, args=[node.source])
        node.rep = self.get_rep(c)

    def visit_SelectMany(self, node):
        self.visit_Select(node)
        node.rep += '.flatten()'

    def visit_Where(self, node):
        if isinstance(node.filter, ast.Lambda):
            lambda_func = node.filter
        elif isinstance(node.filter, ast.Module):
            lambda_func = node.filter.body[0].value
        else:
            raise BaseException('unimplemented where filter: ' + node.filter)
        c = ast.Call(func=lambda_func, args=[node.source])
        node.rep = self.get_rep(node.source) + '[' + self.get_rep(c) + ']'

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
