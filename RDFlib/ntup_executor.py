# Executor and code for the ntup input files
import RDFlib.RDFEventStream

import pandas as pd
import uproot
import ast
import os, sys
from pprint import pprint
import ROOT

class query_ast_visitor(ast.NodeVisitor):
    r"""
    Drive the conversion to C++ from the top level query
    """
    def __init__(self):
        r'''
        Initialize the visitor.
        '''
        # Tracks the output of the code.
        self._var_dict = {}
        self._result = None

    def visit (self, node):
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
        # Next, process the lambda's body.
        self.visit(call_node.func.body)

        # Done processing the lambda. Remove the arguments
        for l_arg in call_node.func.args.args:
            del self._var_dict[l_arg.arg]


    def visit_Attribute(self, call_node):
        'Method call on an object'
        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.value) 
        attr_name = call_node.attr 
        self._result = attr_name

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
        elif type(call_node.func) is ast.BinOp:
            self.visit_Call_Member(call_node)
        elif type(call_node.func) is ast.Attribute:
            self.visit_Call_Member(call_node)
        else:
            raise BaseException("Do not know how to call at " + type(call_node.func).__name__)
        call_node.rep = self._result

    def visit_Tuple(self, tuple_node):
        r'''
        Process a tuple. We visit each component of it, and build up a representation from each result.

        See github bug #21 for the special case of dealing with (x1, x2, x3)[0].
        '''
        tuple_node.rep = tuple(self.get_rep(e) for e in tuple_node.elts)
        self._result = tuple_node.rep

    def visit_CreatePandasDF(self, node):
        'Generate the code to convert to a pandas DF'
        self.generic_visit(node)

    def visit_CreateTTreeFile(self, node):
        '''This AST means we are taking an iterable and converting it to a file.
        '''
        # For each incoming variable, we need to declare something we are going to write.
        var_names = [(name, unique_name(name, is_class_var=True)) for name in node.column_names]
        for cv in var_names:
            self._gc.declare_class_variable('float', cv[1])

        # Next, emit the booking code
        self._gc.add_book_statement(statement.book_ttree("analysis", var_names))

        # For each varable we need to save, put it in the C++ variable we've created above
        # and then trigger a fill statement once that is all done.

        self.generic_visit(node)
        v_rep = self.get_rep(node.source)
        if type(v_rep) is not tuple:
            v_rep = (v_rep,)
        if len(v_rep) != len(var_names):
            raise BaseException("Number of columns ({0}) is not the same as labels ({1}) in TTree creation".format(len(v_rep), len(var_names)))

        for e in zip(v_rep, var_names):
            self._gc.add_statement(statement.set_var(e[1][1], e[0].name()))

        self._gc.add_statement(statement.ttree_fill("analysis"))

        # And we are a terminal, so pop off the block.
        self._gc.pop_scope()

    
    def visit_Select(self, node):
        'Transform the iterable from one form to another'

        # Simulate this as a "call"    
        c = ast.Call(func=node.selection.body[0].value, args=[node.source])
        
        self.visit(c) # return ast.Call(_ast.Lambda, RDFlib.RDFEventStream.RDFFileStream)
        
        node.rep = self._result

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''

        # There isn't any difference between Select and SelectMany here
        self.visit_Select(node)
        node.rep += '.flatten()'


class ntup_executor:
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
        #Output: ast_node.rep, a string with the name of the branches to be included in a new root file.
        qv = query_ast_visitor()
        qv.visit(ast_node)
        data_pathname = self.dataset_source
        
        # open the input root file
        # need to change to read tree name from RDF_example.py
        RDF = ROOT.ROOT.RDataFrame
        file   = RDF("recoTree", data_pathname)

        # colNames contains the names of existing branches that will be passed to the output file
        # defNames contains the names of new branches to be Defined in RDF
        colNames = ROOT.std.vector("string")()
        defNames = ROOT.std.vector("string")()
 
        for col in file.GetColumnNames():
            if col == ast_node.rep:
                colNames.push_back(ast_node.rep)
                
        if (len(colNames)==0):
            defNames.push_back(ast_node.rep)

        output_file = "skimmed.root"    
        for defn in defNames:
            newCol = defn
            newCol = newCol.replace("/", "O")
            newCol = newCol.replace(".0", "")

            file = file.Define(newCol,defn)
            colNames.push_back(newCol)

        if len(colNames)>0:
            file.Snapshot("recoTree", output_file, colNames)
            data_file = uproot.open(output_file)
            ast_node.rep = data_file["recoTree"].pandas.df()

            data_file._context.source.close()

        os.remove(output_file)

        return ast_node.rep #pandas df containing the result