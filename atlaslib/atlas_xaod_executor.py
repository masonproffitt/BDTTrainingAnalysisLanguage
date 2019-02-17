# Executor and code for the ATLAS xaod input files
import tempfile
from shutil import copyfile
import os
from urllib.parse import urlparse
import jinja2
from clientlib.query_ast import query_ast_visitor_base
from atlaslib.generated_code import generated_code
import atlaslib.statement as statement
from atlaslib.expression_ast import assure_labmda
from atlaslib.cpp_representation import cpp_variable

import pandas as pd
import uproot
import ast

class generate_expression_from_lambda(ast.NodeVisitor):
    'Generate code to access an xAOD expression'

    def __init__(self, gc, base_rep):
        'Keep track of the generated code object so we can use it as we need'
        self._gc = gc
        self._var_dict = {}
        self._result = base_rep

    def get_result (self):
        return self._result

    def visit_Lambda(self, lambda_node):
        'Record this variable name so when we see references to it we know it is the event store'
        self._var_dict[lambda_node.args.args[0].arg] = self._result
        ast.NodeVisitor.visit(self, lambda_node.body)
        del self._var_dict[lambda_node.args.args[0].arg]

    def resolve_id (self, id):
        'Look up the in our local dict'
        return self._var_dict[id] if id in self._var_dict else id

    def visit_Call(self, call_node):
        r'''
        We can't deal with arguments, or anything else, so this is a very limited call for now!
        '''
        
        # handle only if this is a call against event.
        object_call_against = self.resolve_id(call_node.func.value.id)
        function_name = call_node.func.attr

        # Make sure we are calling against EVENT.
        if object_call_against is not self._result:
            raise BaseException("Only calls against EVENT are supported")

        # Ok, code up access to the collection.
        c_stub = self._result.name() + ("->" if self._result.is_pointer() else "->")
        self._result = cpp_variable(c_stub + function_name + "()", is_pointer=False)

class query_ast_visitor(query_ast_visitor_base):
    r"""
    Drive the conversion to C++ of the top level query
    """

    def __init__ (self):
        self._gc = generated_code()

    def emit_query(self, e):
        'Emit the parsed lines'
        self._gc.emit_query_code(e)

    def emit_book(self, e):
        'Emit the parsed lines'
        self._gc.emit_book_code(e)

    def visit_panads_df_ast (self, ast):
        ast._source.visit_ast(self)

    def class_declaration_code(self):
        return self._gc.class_declaration_code()

    def visit_ttree_terminal_ast (self, ast):
        'We need to emit the code to generate a TTree as output'

        # For each incoming variable, we need to declare something we are going to write.
        var_names = [(name, "_"+name) for name in ast._column_names]
        self._gc.declare_class_variable ('float', var_names[0][1])

        # Next, emit the booking code
        self._gc.add_book_statement(statement.book_ttree("analysis", [(var_names[0][0], var_names[0][1])]))

        # Get the variable we need to run against.
        ast._source.visit_ast(self)
        v_rep = ast._source.get_rep()

        # Next, fill the variable with something
        self._gc.add_statement(statement.set_var(var_names[0][1], v_rep.name()))
        
        # And trigger a fill!
        self._gc.add_statement(statement.ttree_fill("analysis"))

        # And we are a terminal, so pop off the block.
        self._gc.pop_scope()

    def visit_select_ast (self, select_ast):
        'Figure out what we are selecting'
        # First do the parent.
        query_ast_visitor_base.visit_select_ast(self, select_ast)

        # Get the base rep, and then apply it to the lambda.
        b_rep = select_ast._source.get_rep()
        l = select_ast._selection_function
        assure_labmda(l)
        e_vis = generate_expression_from_lambda(self._gc, b_rep)
        e_vis.visit(l)

        select_ast.set_rep(e_vis.get_result())

    def visit_atlas_file_event_stream_ast(self, ast):
        pass

    def visit_select_many_ast(self, ast):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''
        # Do the visit of the parent stuff first to make sure everything is ready.
        query_ast_visitor_base.visit_select_many_ast(self, ast)

        # Get the collection, and then generate the loop over it.
        rep_source = ast._source.get_rep()
        rep_collection = rep_source.access_collection(self._gc, ast)
        rep_iterator = rep_collection.loop_over_collection(self._gc)

        ast.set_rep(rep_iterator)

class cpp_source_emitter:
    r'''
    Helper class to emit C++ code as we go
    '''
    def __init__(self):
        self._lines_of_query_code = []
        self._indent_level = 0

    def add_line (self, l):
        'Add a line of code, automatically deal with the indent'
        if l == '}':
            self._indent_level -= 1

        self._lines_of_query_code += ["{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def lines_of_query_code (self):
        return self._lines_of_query_code

class atlas_xaod_executor:
    def __init__ (self, dataset):
        self._ds = dataset

    def copy_template_file(self, j2_env, info, template_file, final_dir):
        'Copy a file to a final directory'
        j2_env.get_template(template_file).stream(info).dump(final_dir + '/' + template_file)

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code
        qv = query_ast_visitor()
        ast.visit_ast(qv)
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
            j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
            self.copy_template_file(j2_env, info, 'ATestRun_eljob.py', local_run_dir)
            self.copy_template_file(j2_env, info, 'package_CMakeLists.txt', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.cxx', local_run_dir)
            self.copy_template_file(j2_env, info, 'query.h', local_run_dir)
            self.copy_template_file(j2_env, info, 'runner.sh', local_run_dir)

            # Next, build the control python files by scanning the AST for what is needed

            # Build the C++ file

            # Now use docker to run this mess
            # TODO: Nice error if user doesn't have docker installed or running.
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(local_run_dir, datafile_dir)
            os.system(docker_cmd)
            os.system("type {0}\\query.cxx".format(local_run_dir))

            # Extract the result.
            output_file = "file://{0}/data.root".format(local_run_dir)
            data_file = uproot.open(output_file)
            df = data_file["analysis"].pandas.df()
            data_file._context.source.close()
            return df
