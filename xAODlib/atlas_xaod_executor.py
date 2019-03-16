# Executor and code for the ATLAS xAOD input files
from xAODlib.generated_code import generated_code
import xAODlib.statement as statement
from clientlib.ast_util import assure_lambda, lambda_body
#from xAODlib.AtlasEventStream import AtlasXAODFileStream
import xAODlib.AtlasEventStream
from cpplib.cpp_vars import unique_name
import cpplib.cpp_ast as cpp_ast
from cpplib.cpp_representation import cpp_variable, cpp_collection, name_from_rep, cpp_expression
from clientlib.tuple_simplifier import remove_tuple_subscripts
from clientlib.function_simplifier import simplify_chained_calls
from clientlib.aggregate_shortcuts import aggregate_node_transformer

import pandas as pd
import uproot
import ast
import tempfile
from shutil import copyfile
import os
from urllib.parse import urlparse
import jinja2

# Convert between Python comparisons and C++.
# TODO: Fill out all possible ones
compare_operations = {
    ast.Lt: '<',
    ast.LtE: '<=',
    ast.Gt: '>',
    ast.GtE: '>=',
    ast.Eq: '==',
    ast.NotEq: '!=',
}

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

    def include_files(self):
        return self._gc.include_files()

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

    def get_rep(self, node, use_generic_visit = False, reset_result = None):
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        use_generic_visit - if true do generic_visit rather than visit.
        reset_result - Reset the _result variable to this value if requested.
        '''
        if not hasattr(node, 'rep'):
            self.generic_visit(node) if use_generic_visit else self.visit(node)

        # Reset the result
        if reset_result is not None:
            self._result = reset_result

        return node.rep

    def resolve_id(self, id):
        'Look up the in our local dict'
        return self._var_dict[id] if id in self._var_dict else id

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. This is book keeping and we dive in'

        for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
            self._var_dict[l_arg.arg] = c_arg

        # Next, process the lambda's body.
        self.visit(call_node.func.body)

        # Done processing the lambda. Remove the arguments
        for l_arg in call_node.func.args.args:
            del self._var_dict[l_arg.arg]

    def assure_in_loop(self, collection):
        r'''
        Make sure that we are currently in a loop. For example, if we are
        looking at e.Jets.Aggregate then e.Jets hasn't started a loop. OTOH,
        looking at e.Jets.Select(j => j.pt).Aggregate, then we are already in
        a loop.

        collection: representation of a C++ collection or transformed iterable.
        '''
        if collection.is_iterable:
            return collection
        return collection.loop_over_collection(self._gc)


    def visit_Call_Aggregate(self, node):
        r'''Implement the aggregate algorithm in C++
        
        Our source we loop over, and we count out everything. The final result is whatever it is
        we are counting.

        Possible arguments to the call:

        - (acc lambda): the accumulator is set to the first element, and the lambda is called to
                        update it after that.
        - (const, acc lambda): the accumulator is set to the value, and then the lambda is called to
                        update it on every single element.
        - (start lambda, acc lambda): the accumulator is set to the start lambda call on the first
                        element in the sequence, and then acc is called to update it after that.

        Limitations: only floats for now!
        '''
        # Parse the argument list
        use_first_element_seperately = False
        agg_lambda = None
        init_lambda = None
        init_val = None
        if len(node.args) == 1:
            agg_lambda = node.args[0]
            use_first_element_seperately = True
        elif len(node.args) == 2:
            agg_lambda = node.args[1]
            if type(node.args[0]) is ast.Lambda:
                use_first_element_seperately = True
                init_lambda = node.args[0]
            else:
                init_val = node.args[0]
                use_first_element_seperately = False
        else:
            raise BaseException('Aggregate can have only one or two arguments')

        # Declare the thing that will be a result, and make sure everything above knows about it.
        result = cpp_variable(unique_name("aggResult"), cpp_type="float")
        self._gc.declare_variable(result)

        # We have to initalize the variable to some value, and it depends on how the user
        # is trying to initalie things - first iteration or with a value.
        if use_first_element_seperately:
            is_first_iter = cpp_variable(unique_name("is_first"), cpp_type="bool")
            self._gc.declare_variable(is_first_iter)
            self._gc.add_statement(statement.set_var(is_first_iter, cpp_expression("true")))
        else:
            self._gc.add_statement(statement.set_var(result, self.get_rep(init_val)))

        # Store the scope so we cna pop back to it.
        scope = self._gc.current_scope()

        # Next, get the thing we are going to loop over, and generate the loop.
        # Pull the result out of the main result guy
        collection = self.get_rep(node.func.value)
        collection = self._result

        # Iterate over it now. Make sure we are looping over this thing.
        rep_iterator = self.assure_in_loop(collection)

        # If we have to use the first lambda to set the first value, then we need that code up front.
        if use_first_element_seperately:
            if_first = statement.iftest(cpp_expression(is_first_iter.as_cpp()))
            self._gc.add_statement(if_first)
            self._gc.add_statement(statement.set_var(is_first_iter, cpp_expression("false")))
            first_scope = self._gc.current_scope()

            if init_lambda is not None:
                call = ast.Call(init_lambda, [name_from_rep(rep_iterator)])
                self._gc.add_statement(statement.set_var(result, self.get_rep(call)))
            else:
                self._gc.add_statement(statement.set_var(result, rep_iterator))

            self._gc.set_scope(first_scope)
            self._gc.pop_scope()
            self._gc.add_statement(statement.elsephrase())

        # Perform the agregation function. We need to call it with the value and the accumulator.
        call = ast.Call(agg_lambda, [name_from_rep(result), name_from_rep(rep_iterator)])
        self._gc.add_statement(statement.set_var(result, self.get_rep(call)))

        # Finally, pop the whole thing off.
        self._gc.set_scope(scope)

        # Cache the results in our result incase we are skipping nodes in the AST.
        node.rep = result
        self._result = result

    def visit_Call_Member(self, call_node):
        'Method call on an object'

        # If this is a special type of Function call that we need to work with, split out here
        # before any processing is done.
        if (call_node.func.attr == "Aggregate"):
            return self.visit_Call_Aggregate(call_node)

        # Visit everything down a level.
        self.generic_visit(call_node)

        # figure out what we are calling against, and the
        # method name we are going to be calling against.
        calling_against = self.get_rep(call_node.func.value)
        function_name = call_node.func.attr

        # We support member calls that directly translate only. Here, for example, this is only for
        # obj.pt() or similar. The translation is direct.
        c_stub = calling_against.name() + ("->" if calling_against.is_pointer() else "->")
        self._result = cpp_expression(c_stub + function_name + "()")

    def visit_Name(self, name_node):
        'Visiting a name - which should represent something'
        id = self.resolve_id(name_node.id)
        if isinstance(id, ast.AST):
            name_node.rep = self.get_rep(id)

    def visit_Call(self, call_node):
        r'''
        Very limited call forwarding.
        '''
        # What kind of a call is this?
        if type(call_node.func) is ast.Lambda:
            self.visit_Call_Lambda(call_node)
        elif type(call_node.func) is ast.Attribute:
            self.visit_Call_Member(call_node)
        elif type(call_node.func) is cpp_ast.CPPCodeValue:
            self._result = cpp_ast.process_ast_node(self, self._gc, self._result, call_node)
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

    def visit_BinOp(self, node):
        'An in-line add'
        left = self.get_rep(node.left)
        right = self.get_rep(node.right)

        if type(node.op) is ast.Add:
            r = cpp_expression("({0}+{1})".format(left.as_cpp(), right.as_cpp()))
        else:
            raise BaseException("Binary operator {0} is not implemented.".format(type(node.op)))

        # Cache the result to push it back further up.
        node.rep = r
        self._result = r

    def visit_IfExp(self, node):
        r'''
        We'd like to be able to use the "?" operator in C++, but the
        problem is lazy evaluation. It could be when we look at one or the
        other item, a bunch of prep work has to be done - and that will
        show up in seperate statements. So we have to use if/then/else with
        a result value.
        '''
        
        # The result we'll store everything in.
        result = cpp_variable(unique_name("ifelse_result"), cpp_type="float")
        self._gc.declare_variable(result)

        # We always have to evaluate the test.
        current_scope = self._gc.current_scope()
        test_expr = self.get_rep(node.test)
        self._gc.add_statement(statement.iftest(test_expr))
        if_scope = self._gc.current_scope()

        # Next, we do the true and false if statement.
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.body)))
        self._gc.set_scope(if_scope)
        self._gc.pop_scope()
        self._gc.add_statement(statement.elsephrase())
        self._gc.add_statement(statement.set_var(result, self.get_rep(node.orelse)))
        self._gc.set_scope(current_scope)

        # Done, the result is the rep of this node!
        node.rep = result
        self._result = result

    def visit_Compare(self, node):
        'A compare between two things. Python supports more than that, but not implemented yet.'
        if len(node.ops) != 1:
            raise BaseException("Do not support 1 < a < 10 comparisons yet!")
        
        left = self.get_rep(node.left)
        right = self.get_rep(node.comparators[0])

        r = cpp_expression('({0}{1}{2})'.format(left.as_cpp(), compare_operations[type(node.ops[0])], right.as_cpp()))
        node.rep = r
        self._result = r

    def visit_Num(self, node):
        node.rep = cpp_expression(node.n)
        self._result = node.rep

    def visit_CreatePandasDF(self, node):
        'Generate the code to convert to a pandas DF'
        self.generic_visit(node)

    def visit_CreateTTreeFile(self, node):
        '''This AST means we are taking an iterable and converting it to a file.
        '''
        # For each incoming variable, we need to declare something we are going to write.
        var_names = [(name, cpp_variable(unique_name(name, is_class_var=True), cpp_type="float")) for name in node.column_names]
        for cv in var_names:
            self._gc.declare_class_variable(cv[1])

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
            self._gc.add_statement(statement.set_var(e[1][1], e[0]))

        self._gc.add_statement(statement.ttree_fill("analysis"))

        # And we are a terminal, so pop off the block.
        self._gc.pop_scope()

    def visit_Select(self, select_ast):
        'Transform the iterable from one form to another'

        s_rep = self.get_rep(select_ast.source)
        selection = select_ast.selection.body[0].value

        # Make sure we are in a loop
        loop_var = self.assure_in_loop(s_rep)
        s_ast = select_ast.source if loop_var is s_rep else name_from_rep(loop_var)

        # Simulate this as a "call"
        c = ast.Call(func=selection, args=[s_ast])
        self.visit(c)

        rep = self._result
        if type(rep) is not tuple:
            rep.is_iterable = True
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
        j2_env.get_template(template_file).stream(info).dump(final_dir + '/' + template_file)
    
    def apply_ast_transformations(self, ast):
        r'''
        Run through all the transformations that we have on tap to be run on the client side.
        Return a (possibly) modified ast.
        '''

        # Do tuple resolutions. This might eliminate a whole bunch fo code!
        #TODO: Remove this debugging line
        from clientlib.ast_util import pretty_print

        ast = aggregate_node_transformer().visit(ast)
        ast = simplify_chained_calls().visit(ast)
        ast = remove_tuple_subscripts().visit(ast)

        # Any C++ custom code needs to be threaded into the ast
        ast = cpp_ast.cpp_ast_finder().visit(ast)

        # And return the modified ast
        return ast

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
        includes = qv.include_files()

        # Create a temp directory in which we can run everything.
        with tempfile.TemporaryDirectory() as local_run_dir:
            os.chmod(local_run_dir, 0o777)

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
            info['include_files'] = includes

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

            os.chmod(os.path.join(local_run_dir, 'runner.sh'), 0o755)

            # Next, build the control python files by scanning the AST for what is needed

            # Build the C++ file

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(
                local_run_dir, datafile_dir)
            os.system(docker_cmd)
            os.system("type " + os.path.join(local_run_dir, "query.cxx"))

            # Extract the result.
            output_file = "file://{0}/data.root".format(local_run_dir)
            data_file = uproot.open(output_file)
            df = data_file["analysis"].pandas.df()
            data_file._context.source.close()
            return df
