# Executor and code for the ATLAS xAOD input files
import tempfile
from shutil import copyfile
import os
from urllib.parse import urlparse
import jinja2
from xAODlib.generated_code import generated_code
import xAODlib.statement as statement
from xAODlib.expression_ast import assure_lambda
from xAODlib.cpp_representation import cpp_variable, cpp_collection
#from xAODlib.AtlasEventStream import AtlasXAODFileStream
import xAODlib.AtlasEventStream
from xAODlib.cpp_vars import unique_name


import pandas as pd
import uproot
import ast


class query_ast_visitor(ast.NodeVisitor):
    r"""
    Drive the conversion to C++ from the top level query
    """

    def __init__(self):
        r'''
        Initialize the visitor.
        '''
        # Tracks the output of the code.
        self._gc = generated_code()
        self._var_dict = {}
        self._result = None

    def emit_query(self, e):
        'Emit the parsed lines'
        self._gc.emit_query_code(e)

    def emit_book(self, e):
        'Emit the parsed lines'
        self._gc.emit_book_code(e)

    def class_declaration_code(self):
        return self._gc.class_declaration_code()

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

    def get_rep(self, node, use_generic_visit = False):
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        use_generic_visit - if true do generic_visit rather than visit.
        '''
        if not hasattr(node, 'rep'):
            self.generic_visit(node) if use_generic_visit else self.visit(node)

        return node.rep

    def resolve_id(self, id):
        'Look up the in our local dict'
        return self._var_dict[id] if id in self._var_dict else id

    def call_against_current_obj(self, obj, object_call_method, args):
        'Call against the current object'
        c_stub = obj.name() + ("->" if obj.is_pointer() else "->")
        self._result = cpp_variable(
            c_stub + object_call_method + "()", is_pointer=False)
        pass

    def call_base_collection(self, object_call_method, args):
        'Call against the base collection'
        if object_call_method == "Jets":
            collection_name = args[0].s
            self._gc.add_statement(
                statement.xaod_get_collection(collection_name, "jets"))
            self._result = cpp_collection("jets", is_pointer=True)
        else:
            raise BaseException("Only Jets is understood right now")

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. This is book keeping and we dive in'

        for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
            self._var_dict[l_arg.arg] = c_arg

        # Next, process the lambda's body.
        self.visit(call_node.func.body)

        # Done processing the lambda. Remove the arguments
        for l_arg in call_node.func.args.args:
            del self._var_dict[l_arg.arg]

    def visit_Call_Member(self, call_node):
        'Method call on an object'

        # This is a 'real' call - that is, something we should know about rather than
        # arbitrary python code.
        object_call_against = self.resolve_id(call_node.func.value.id)
        function_name = call_node.func.attr

        # Make sure the thing we are calling against has been "parsed"
        self.visit(object_call_against)

        # Calls are different depending upon what they are against.
        #  - Global space - then it is a function (like "sin" or "len")
        #  - an object - some object we know something about
        #  - The ROOT object collection.
        if type(object_call_against) is xAODlib.AtlasEventStream.AtlasXAODFileStream:
            self.call_base_collection(function_name, call_node.args)
        else:
            self.call_against_current_obj(
                object_call_against.rep, function_name, call_node.args)

    def visit_Call(self, call_node):
        r'''
        Very limited call forwarding.
        '''
        # What kind of a call is this?
        if type(call_node.func) is ast.Lambda:
            self.visit_Call_Lambda(call_node)
        else:
            self.visit_Call_Member(call_node)
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

    def visit_Select(self, select_ast):
        'Transform the iterable from one form to another'

        # Simulate this as a "call"
        c = ast.Call(func=select_ast.selection.body[0].value, args=[
                     select_ast.source])
        self.visit(c)

        rep = self._result
        select_ast.rep = rep

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''
        # We need to "call" the source with the function. So build up a new
        # call, and then visit it.

        c = ast.Call(func=node.selection.body[0].value, args=[node.source])
        self.visit(c)

        # The result is the collection we need to be looking at.
        rep_collection = self._result

        # Get the collection, and then generate the loop over it.
        rep_iterator = rep_collection.loop_over_collection(self._gc)

        node.rep = rep_iterator


class cpp_source_emitter:
    r'''
    Helper class to emit C++ code as we go
    '''

    def __init__(self):
        self._lines_of_query_code = []
        self._indent_level = 0

    def add_line(self, l):
        'Add a line of code, automatically deal with the indent'
        if l == '}':
            self._indent_level -= 1

        self._lines_of_query_code += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def lines_of_query_code(self):
        return self._lines_of_query_code


class atlas_xaod_executor:
    def __init__(self, dataset):
        self._ds = dataset

    def copy_template_file(self, j2_env, info, template_file, final_dir):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(
            info).dump(final_dir + '/' + template_file)

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code
        qv = query_ast_visitor()
        qv.visit(ast)
        query_code = cpp_source_emitter()
        qv.emit_query(query_code)
        book_code = cpp_source_emitter()
        qv.emit_book(book_code)
        class_dec_code = qv.class_declaration_code()

        # Create a temp directory in which we can run everything.
        with tempfile.TemporaryDirectory() as local_run_dir:

            # Parse the dataset. Eventually, this needs to be normalized, but for now.
            (_, netloc, path, _, _, _) = urlparse(self._ds)
            datafile = netloc + path
            datafile_dir = os.path.dirname(datafile)
            datafile_name = os.path.basename(datafile)
            info = {}
            info['data_file_name'] = datafile_name
            info['query_code'] = query_code.lines_of_query_code()
            info['book_code'] = book_code.lines_of_query_code()
            info['class_dec'] = class_dec_code

            # Next, copy over and fill the template files
            template_dir = "./R21Code"
            j2_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir))
            self.copy_template_file(
                j2_env, info, 'ATestRun_eljob.py', local_run_dir)
            self.copy_template_file(
                j2_env, info, 'package_CMakeLists.txt', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.cxx', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.h', local_run_dir)
            self.copy_template_file(j2_env, info, 'runner.sh', local_run_dir)

            # Next, build the control python files by scanning the AST for what is needed

            # Build the C++ file

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(
                local_run_dir, datafile_dir)
            os.system(docker_cmd)
            os.system("type {0}\\query.cxx".format(local_run_dir))

            # Extract the result.
            output_file = "file://{0}/data.root".format(local_run_dir)
            data_file = uproot.open(output_file)
            df = data_file["analysis"].pandas.df()
            data_file._context.source.close()
            return df
