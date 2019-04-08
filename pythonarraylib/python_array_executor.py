#from clientlib.aggregate_shortcuts import aggregate_node_transformer

import ast
import os

class python_array_ast_visitor(ast.NodeVisitor):
    r"""
    Drive the conversion to awkward from the top level query
    """

    def __init__(self):
        r'''
        Initialize the visitor.
        '''
        self._var_dict = {}
        self._result = None

    def visit(self, node):
        '''Visit a note. If the node already has a rep, then it has been visited and we
        do not need to visit it again.

        node - if the node has a rep, just return

        '''
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.visit(self, node)

    def generic_visit(self, node):
        '''Visit a generic node. If the node already has a rep, then it has been
        visited once and we do not need to visit it again.

        node - If the node has a rep, do not visit it.
        '''
        if hasattr(node, 'rep'):
            return
        else:
            return ast.NodeVisitor.generic_visit(self, node)

    def get_rep(self, node):
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        '''
        if not hasattr(node, 'rep'):
            self.visit(node)
        #print(node)
        print(ast.dump(node))
        return node.rep

    def resolve_id(self, id):
        'Look up the in our local dict'
        if id in self._var_dict:
            id = self._var_dict[id]
        if isinstance(id, ast.AST):
            id = self.get_rep(id)
        return id

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. This is book keeping and we dive in'

        for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
            self._var_dict[l_arg.arg] = c_arg

        ## Next, process the lambda's body.
        #self.visit(call_node.func.body)
        call_node.rep = self.get_rep(call_node.func.body)

        ## Done processing the lambda. Remove the arguments
        for l_arg in call_node.func.args.args:
            del self._var_dict[l_arg.arg]

    def visit_Call_Aggregate(self, node):
        if len(node.args) == 2:
            if type(node.args[0]) is ast.Lambda:
                raise BaseException('not really sure how this kind of aggregate works...')
            else:
                init_value = node.args[0]
                agg_lambda = node.args[1]
        else:
            raise BaseException('not really sure how this kind of aggregate works...')
        #node.rep = 'for ' + ' in ' + self.get_rep(node.func.value) + ':\n'
        #node.rep += '    '

    def visit_Call_Member(self, call_node):
        'Method call on an object'
        if (call_node.func.attr == "Aggregate"):
            return self.visit_Call_Aggregate(call_node)

    def visit_Attribute(self, call_node):
        'Method call on an object'

        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.value)

        attr_name = call_node.attr

        #self._result = calling_against + "['" + attr_name + "']"
        call_node.rep = calling_against + "['" + attr_name + "']"

    def visit_Name(self, name_node):
        'Visiting a name - which should represent something'
        name_node.rep = self.resolve_id(name_node.id)

    def visit_Call(self, call_node):
        r'''
        Very limited call forwarding.
        '''
        # What kind of a call is this?
        if type(call_node.func) is ast.Lambda:
            self.visit_Call_Lambda(call_node)
        elif type(call_node.func) is ast.Attribute:
            self.visit_Call_Member(call_node)
        elif type(call_node.func) is ast.Name:
            print('in visit_Call:Name')
            if (call_node.func.id == 'len') and (len(call_node.args) == 1):
                print("it's len")
                #self._result = self.get_rep(call_node.args[0]) + '.size'
                call_node.rep = self.get_rep(call_node.args[0]) + '.size'
                #print(call_node.rep)
                #new_call = ast.Call(func=ast.Attribute(attr="Count", value=call_node.args[0]))
        else:
            raise BaseException("Do not know how to call at " + type(call_node.func).__name__)
        #call_node.rep = self._result

    def visit_Tuple(self, node):
        node.rep = '(' + ''.join(self.get_rep(e) + ', ' for e in node.elts) + ')'

    def visit_Select(self, node):
        'Transform the iterable from one form to another'

        c = ast.Call(func=node.selection.body[0].value, args=[node.source])
        #self.visit(c)
        #node.rep = self._result
        node.rep = self.get_rep(c)

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''

        # There isn't any difference between Select and SelectMany here
        self.visit_Select(node)
        node.rep += '.flatten()'

class python_array_executor:
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source

    def apply_ast_transformations(self, ast):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''
        #ast = aggregate_node_transformer().visit(ast)
        return ast
