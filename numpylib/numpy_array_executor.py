import ast
import numpy
import os

class ast_visitor(ast.NodeVisitor):
    r"""
    Drive the conversion to numpy from the top level query
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
        self.visit(call_node.func.body)

        ## Done processing the lambda. Remove the arguments
        for l_arg in call_node.func.args.args:
            del self._var_dict[l_arg.arg]

    def visit_Attribute(self, call_node):
        'Method call on an object'

        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.value)

        attr_name = call_node.attr

        self._result = calling_against + "['" + attr_name + "']"

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
        else:
            raise BaseException("Do not know how to call at " + type(call_node.func).__name__)
        call_node.rep = self._result

    def visit_Select(self, node):
        'Transform the iterable from one form to another'

        c = ast.Call(func=node.selection.body[0].value, args=[node.source])
        self.visit(c)
        node.rep = self._result

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''

        # There isn't any difference between Select and SelectMany here
        self.visit_Select(node)
        node.rep += '.flatten()'

class numpy_array_executor:
    def __init__(self, dataset_source):
        self.dataset_source = dataset_source

    def apply_ast_transformations(self, ast):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''
        return ast

    def evaluate(self, ast_node):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code
        qv = ast_visitor()
        print(ast.dump(ast_node))
        qv.visit(ast_node)
        if isinstance(self.dataset_source, numpy.ndarray):
            data_pathname = 'temp.npy'
            numpy.save(data_pathname, self.dataset_source)
        else:
            data_pathname = self.dataset_source
        f = open('temp.py', 'w')
        f.write('import numpy\n')
        source = ast_node.source
        while hasattr(source, 'source'):
            source = source.source
        f.write(source.rep + " = numpy.load('" + data_pathname + "')\n")
        f.write('output_array = ' + ast_node.rep + '\n')
        f.write("numpy.save('output.npy', output_array)\n")
        f.close()
        os.system('python temp.py')
        if isinstance(self.dataset_source, numpy.ndarray):
            os.remove(data_pathname)
        os.remove('temp.py')
        output = numpy.load('output.npy')
        os.remove('output.npy')
        return output
