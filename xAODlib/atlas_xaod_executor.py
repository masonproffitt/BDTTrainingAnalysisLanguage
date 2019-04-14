# Executor and code for the ATLAS xAOD input files
from xAODlib.generated_code import generated_code, scope_is_deeper
import xAODlib.statement as statement
from clientlib.ast_util import lambda_assure, lambda_body, lambda_unwrap
from cpplib.cpp_vars import unique_name
import cpplib.cpp_ast as cpp_ast
from cpplib.cpp_representation import cpp_variable, cpp_collection, cpp_expression, cpp_tuple, cpp_iterator_over_collection, cpp_constant, cpp_forward_capture
import xAODlib.result_handlers as rh
import clientlib.query_result_asts as query_result_asts
from clientlib.call_stack import argument_stack, stack_frame

from clientlib.tuple_simplifier import remove_tuple_subscripts
from clientlib.function_simplifier import simplify_chained_calls
from clientlib.aggregate_shortcuts import aggregate_node_transformer
from cpplib.cpp_functions import find_known_functions, function_ast

import ast
import tempfile
from shutil import copyfile
import os
import subprocess
import sys
from urllib.parse import urlparse
import jinja2
from copy import copy

# Use this to turn on dumping of output and C++
dump_cpp = False
dump_running_log = True

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

# Result handlers - for each return type representation, add a handler that can process it
result_handlers = {
        rh.cpp_ttree_rep: rh.extract_result_TTree,
        rh.cpp_awkward_rep: rh.extract_awkward_result,
        rh.cpp_pandas_rep: rh.extract_pandas_result,
}

def rep_is_collection(rep):
    'Return true if the representation points to a collection'
    if type(rep) is cpp_iterator_over_collection:
        return True
    elif rep.is_iterable:
        return True
    return False

def type_of_rep(rep):
    '''
    Return a float unless it is an iterable. Then it is a vector of float.
    '''
    if rep_is_collection(rep):
        return "std::vector<float>"
    return "float"

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
        self._arg_stack = argument_stack()
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
        '''Visit a node. If the node already has a rep, then it has been visited and we
        do not need to visit it again.

        node - if the node has a rep, just return

        '''
        if hasattr(node, 'rep'):
            self._result = node.rep
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

    def get_rep(self, node, use_generic_visit = False, reset_result = None, retain_scope = False):
        r'''Return the rep for the node. If it isn't set yet, then run our visit on it.

        node - The ast node to generate a representation for.
        use_generic_visit - if true do generic_visit rather than visit.
        reset_result - Reset the _result variable to this value if requested.
        retain_scope - If true, then the scope level will remain the same before and after the call.
        '''
        if not hasattr(node, 'rep'):
            s = self._gc.current_scope() if retain_scope else None
            self.generic_visit(node) if use_generic_visit else self.visit(node)
            if retain_scope:
                self._gc.set_scope(s)

        # Reset the result
        if reset_result is not None:
            self._result = reset_result

        # If it still didn't work, this is an internal error. But make the error message a bit nicer.
        if not hasattr(node, 'rep'):
            raise BaseException('Internal Error: attempted to get C++ representation for AST note "{0}", but failed.'.format(ast.dump(node)))
        return node.rep

    def get_rep_iterator(self, node):
        'For nodes that are generating sequences, returns the iterator attached'
        r = self.get_rep(node)
        return r.find_best_iterator()

    def resolve_id(self, id):
        'Look up the in our local dict'
        return self._arg_stack.lookup_name(id)

    def visit_Call_Lambda(self, call_node):
        'Call to a lambda function. This is book keeping and we dive in'

        with stack_frame(self._arg_stack):
            for c_arg, l_arg in zip(call_node.args, call_node.func.args.args):
                self._arg_stack.define_name(l_arg.arg, c_arg)

            # Next, process the lambda's body.
            call_node.rep = self.get_rep(call_node.func.body)
            lp = self.get_rep_iterator(call_node.func.body)
        
            
    def assure_in_loop(self, generation_ast):
        r'''
        Make sure that we are currently in a loop. For example, if we are
        looking at e.Jets.Aggregate then e.Jets hasn't started a loop. OTOH,
        looking at e.Jets.Select(j => j.pt).Aggregate, then we are already in
        a loop.

        generation_ast - The AST that will generate the collection (a call to something that
                         returns a collection or a Select statement, etc.)

        iterator:       This is the collection or iterator that is in the inside of the loop.
                        If this has been modified by a Select statement, for example, then return
                        the thing that points to that.
        loop_var:       The variable that is the loop we are running over. If this is the top level of a loop
                        this would be the same as `iterator`.
        '''
        # Get the representation of the collection. This will be one of several things:
        #  - The collection itself (like a vector<..>)
        #  - A variable that is already iterating over the collection.
        #    For example, if the thing before caused a loop to be generated already.
        # If we have an associated loop variable, then are set, and we can return it all.
        loop_var = self.get_rep_iterator(generation_ast)
        c_iter = self.get_rep(generation_ast)
        if loop_var is not None:
            return (c_iter, loop_var)

        # So, no loop variable. If the iterator is iterable, then
        # there should have been an iterator.
        if c_iter.is_iterable:
            raise BaseException("Internal Error: A variable that can iterate, but no partner loop variable ('{0}')".format(c_iter.as_cpp()))

        # Last ditch effort - try to generate a loop over the thing. In short, this is a collection that
        # can be iterated over. Since it is a collection, it doesn't really have an iterator - so we don't
        # attach one.
        # In this case the iterator and the loop variable are the same.
        if not hasattr(c_iter, "loop_over_collection"):
            # Make the error message a bit more understandable.
            raise BaseException('Do not know how to loop over the expression "{0}" (with type info: {1}).'.format(c_iter.as_cpp(), c_iter.cpp_type()))

        c_loop_var = c_iter.loop_over_collection(self._gc)
        return (c_loop_var, c_loop_var)


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
        use_first_element_separately = False
        agg_lambda = None
        init_lambda = None
        if len(node.args) == 1:
            agg_lambda = node.args[0]
            use_first_element_separately = True
        elif len(node.args) == 2:
            agg_lambda = node.args[1]
            if type(node.args[0]) is ast.Lambda:
                use_first_element_separately = True
                init_lambda = node.args[0]
            else:
                init_val = node.args[0]
                use_first_element_separately = False
        else:
            raise BaseException('Aggregate can have only one or two arguments')

        # Get all the looping information
        (c_iter, c_loop) = self.assure_in_loop(node.func.value)

        # We need to store the result. It should be outside the loop variable we are looping over.
        decl_block_scope = (c_loop.scope()[0][:-1],)
        decl_block = decl_block_scope[0][-1]
        result = cpp_variable(unique_name("aggResult"), decl_block_scope, cpp_type="float", initial_value="0" if not use_first_element_separately else None)
        decl_block.declare_variable(result)

        # We have to initialized the variable to some value, and it depends on how the user
        # is trying to initialize things - first iteration or with a value. We've done the value case above.
        is_first_iter = None
        if use_first_element_separately:
            is_first_iter = cpp_variable(unique_name("is_first"), self._gc.current_scope(), cpp_type="bool", initial_value='true')
            decl_block.declare_variable(is_first_iter)

        # Now we need to emit code at the accumulator level.
        self._gc.set_scope(c_loop.scope())

        # If we have to use the first lambda to set the first value, then we need that code up front.
        if use_first_element_separately:
            if_first = statement.iftest(cpp_constant(is_first_iter.as_cpp()))
            self._gc.add_statement(if_first)
            self._gc.add_statement(statement.set_var(is_first_iter, cpp_constant("false")))
            first_scope = self._gc.current_scope()

            if init_lambda is not None:
                call = ast.Call(init_lambda, [c_iter.as_ast()])
                self._gc.add_statement(statement.set_var(result, self.get_rep(call)))
            else:
                self._gc.add_statement(statement.set_var(result, c_iter))

            self._gc.set_scope(first_scope)
            self._gc.pop_scope()
            self._gc.add_statement(statement.elsephrase())

        # Perform the aggregation function. We need to call it with the value and the accumulator.
        call = ast.Call(func=agg_lambda, args=[result.as_ast(), c_iter.as_ast()])
        self._gc.add_statement(statement.set_var(result, self.get_rep(call)))

        # Finally, since this is a terminal, we need to pop off the top.
        self._gc.set_scope(decl_block_scope)

        # Cache the results in our result incase we are skipping nodes in the AST.
        node.rep = result
        self._result = result

    def visit_Call_Member(self, call_node):
        'Method call on an object'

        # If this is a special type of Function call that we need to work with, split out here
        # before any processing is done.
        # TODO: Support arguments to functions like this.
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
        # TODO: The iterator might be in an argument, so passing calling_against here may not be ok.
        c_stub = calling_against.as_cpp() + ("->" if calling_against.is_pointer() else ".")
        self._result = cpp_expression(c_stub + function_name + "()", calling_against, calling_against.scope(), the_ast = call_node)

    def visit_function_ast(self, call_node):
        'Drop-in replacement for a function'
        # Get the arguments
        cpp_func = call_node.func
        arg_reps = [self.get_rep(a) for a in call_node.args]

        # Code up a call
        # TODO: The iterator might not be Note.
        r = cpp_expression('{0}({1})'.format(cpp_func.cpp_name, ','.join(a.as_cpp() for a in arg_reps)), [cpp_func] + arg_reps, self._gc.current_scope(), cpp_type = cpp_func.cpp_return_type)

        # Include files and return the resulting expression
        for i in cpp_func.include_files:
            self._gc.add_include(i)
        call_node.rep = r
        return r

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
        elif type(call_node.func) is function_ast:
            self._result = self.visit_function_ast(call_node)
        else:
            raise BaseException("Do not know how to call '{0}'".format(ast.dump(call_node.func, annotate_fields=False)))
        call_node.rep = self._result

    def visit_Name(self, name_node):
        'Visiting a name - which should represent something'
        id = self.resolve_id(name_node.id)
        if isinstance(id, ast.AST):
            name_node.rep = self.get_rep(id)

    def visit_Subscript(self, node):
        'Index into an array. Check types, as tuple indexing can be very bad for us'
        v = self.get_rep(node.value)
        if v.cpp_type() != 'std::vector<double>':
            raise BaseException("Do not know how to take the index of type '{0}'".format(v.cpp_type()))
        index = self.get_rep(node.slice)
        # TODO: extract the type from the expression
        node.rep = cpp_expression("{0}.at({1})".format(v.as_cpp(), index.as_cpp()), [v, index], self._gc.current_scope(), cpp_type="double")
        self._result = node.rep

    def visit_Index(self, node):
        'We can only do single items, we cannot do slices yet'
        v = self.get_rep(node.value)
        node.rep = v
        self._result = node

    def visit_Tuple(self, tuple_node):
        r'''
        Process a tuple. We visit each component of it, and build up a representation from each result.

        See github bug #21 for the special case of dealing with (x1, x2, x3)[0].
        '''
        tuple_node.rep = cpp_tuple(tuple(self.get_rep(e, retain_scope=True) for e in tuple_node.elts), self._gc.current_scope())
        self._result = tuple_node.rep

    def visit_BinOp(self, node):
        'An in-line add'
        left = self.get_rep(node.left)
        right = self.get_rep(node.right)

        if type(node.op) is ast.Add:
            r = cpp_expression("({0}+{1})".format(left.as_cpp(), right.as_cpp()), [left, right], self._gc.current_scope())
        elif type(node.op) is ast.Div:
            r = cpp_expression("({0}/{1})".format(left.as_cpp(), right.as_cpp()), [left, right], self._gc.current_scope())
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
        show up in separate statements. So we have to use if/then/else with
        a result value.
        '''
        
        # The result we'll store everything in.
        result = cpp_variable(unique_name("if_else_result"), self._gc.current_scope(), cpp_type="float")
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

        r = cpp_expression('({0}{1}{2})'.format(left.as_cpp(), compare_operations[type(node.ops[0])], right.as_cpp()), [left, right], self._gc.current_scope())
        node.rep = r
        self._result = r

    def visit_BoolOp(self, node):
        '''A bool op like And or Or on a set of values
        This is a bit more complex than just "anding" things as we want to make sure to short-circuit the
        evaluation if we need to.
        '''

        # The result of this test
        result = cpp_variable(unique_name('bool_op'), self._gc.current_scope(), cpp_type='bool')
        self._gc.declare_variable (result)

        # How we check and short-circuit depends on if we are doing and or or.
        check_expr = result.as_cpp() if type(node.op) == ast.And else '!{0}'.format(result.as_cpp())
        check = cpp_expression(check_expr, result, self._gc.current_scope(), cpp_type='bool')

        first = True
        scope = self._gc.current_scope()
        for v in node.values:
            if not first:
                self._gc.add_statement(statement.iftest(check))

            rep_v = self.get_rep(v)
            self._gc.add_statement(statement.set_var(result, rep_v))

            if not first:
                self._gc.set_scope(scope)
            first = False
        
        # Cache result variable so those above us have something to use.
        self._result = result
        node.rep = result


    def visit_Num(self, node):
        node.rep = cpp_constant(node.n)
        self._result = node.rep

    def visit_Str(self, node):
        node.rep = cpp_constant('"{0}"'.format(node.s))
        self._result = node.rep

    def visit_resultTTree(self, node):
        '''This AST means we are taking an iterable and converting it to a ROOT file.
        '''
        # Get the representations for each variable.
        self.generic_visit(node)
        (v_rep_not_norm, v_loop) = self.assure_in_loop(node.source)
        #v_rep_not_norm = self.get_rep(node.source)
        v_rep_not_norm = v_rep_not_norm.get_underlying_object()
        v_rep = v_rep_not_norm.tup() if type(v_rep_not_norm) is cpp_tuple else (v_rep_not_norm,)

        # Check for something weird, like a 2D array.
        if (type(v_rep_not_norm) is cpp_iterator_over_collection) and (type(v_rep_not_norm.iter().get_underlying_object()) is cpp_tuple):
            raise BaseException("Looks like you have asked for a 2D array which is not yet supported (you have a tuple inside a select sequence)")

        # Make sure the number of items is the same as the number of columns specified.
        if len(v_rep) != len(node.column_names):
            raise BaseException("Number of columns ({0}) is not the same as labels ({1}) in TTree creation".format(len(v_rep), len(node.column_names)))

        # Next, look at each on in turn to decide if it is a vector or a simple variable.
        var_names = [(name, cpp_variable(unique_name(name, is_class_var=True), self._gc.current_scope(), cpp_type=type_of_rep(rep))) 
                    for name, rep in zip(node.column_names, v_rep)]

        # For each incoming variable, we need to declare something we are going to write.
        for cv in var_names:
            self._gc.declare_class_variable(cv[1])

        # Next, emit the booking code
        tree_name = unique_name("analysis_tree")
        self._gc.add_book_statement(statement.book_ttree(tree_name, var_names))

        # Note that the output file and tree are what we are going to return.
        node.rep = rh.cpp_ttree_rep("data.root", tree_name, self._gc.current_scope())

        # For each varable we need to save, cache it or push it back, depending.
        # Make sure that it happens at the proper scope, where what we are after is defined!
        s_orig = self._gc.current_scope()
        for e_rep,e_name in zip(v_rep, var_names):
            # Set the scope. Normally we want to do it where the variable was calculated
            # (think of cases when you have to calculate something with a `push_back`),
            # but if the variable was already calculated, we want to make sure we are at least
            # in the same scope as the tree fill.
            if scope_is_deeper(e_rep.scope(), v_rep_not_norm.scope()):
                self._gc.set_scope(v_rep_not_norm.scope())
            else:
                self._gc.set_scope(e_rep.scope())

            # If the variable is something we are iterating over, then fill it, otherwise,
            # just set it.
            if rep_is_collection(e_rep):
                self._gc.add_statement(statement.push_back(e_name[1], e_rep))
            else:
                self._gc.add_statement(statement.set_var(e_name[1], e_rep))

        # The fill statement. This should happen at the scope where the tuple was defined.
        defined_scope = self.get_rep_iterator(node.source)
        self._gc.set_scope(defined_scope.scope() if defined_scope is not None else ([],))
        self._gc.add_statement(statement.ttree_fill(tree_name))
        for e in zip(v_rep, var_names):
            if rep_is_collection(e[0]):
                self._gc.add_statement(statement.container_clear(e[1][1]))

        # And we are a terminal, so pop off the block.
        self._gc.set_scope(s_orig)
        self._gc.pop_scope()

    def visit_resultAwkwardArray(self, node):
        '''
        The result of this guy is an awkward array. We generate a token here, and invoke the resultTTree in order to get the
        actual ROOT file written. Later on, when dealing with the result stuff, we extract it into an awkward array.
        '''
        ttree = query_result_asts.resultTTree(node.source, node.column_names)
        r = self.get_rep(ttree)
        node.rep = rh.cpp_awkward_rep(r.filename, r.treename, self._gc.current_scope())
        self._result = node.rep

    def visit_resultPandasDF(self, node):
        '''
        The result of this guy is an pandas dataframe. We generate a token here, and invoke the resultTTree in order to get the
        actual ROOT file written. Later on, when dealing with the result stuff, we extract it into an awkward array.
        '''
        ttree = query_result_asts.resultTTree(node.source, node.column_names)
        r = self.get_rep(ttree)
        node.rep = rh.cpp_pandas_rep(r.filename, r.treename, self._gc.current_scope())
        self._result = node.rep

    def visit_Select(self, select_ast):
        'Transform the iterable from one form to another'

        # Make sure we are in a loop
        (c_iter, loop_var) = self.assure_in_loop(select_ast.source)

        # Remember the scope so that we can make sure we are still at this level when we come back.
        start_scope = self._gc.current_scope()

        # Simulate this as a "call"
        selection = lambda_unwrap(select_ast.selection)
        c = ast.Call(func=selection, args=[c_iter.as_ast()])
        rep = self.get_rep(c)

        # Now, we need to mark this as iterable. But this is a little tricky how this is done.
        # If this is a value (like j->pt()), then this just becomes a simple sequence. So we
        # can just mark it. However, if this is already a sequence, then we are doing a sequence
        # of a sequence. So we need to create a new guy for that so that we can deal with the loop
        # correctly. That done - we still want to make sure we are iterating over this guy.
        # There is a final special case - if this is at the top level of an event, then this
        # isn't iterable - there is only one of these per event (even if there are many per
        # file)
        if rep.is_iterable:
            rep = cpp_iterator_over_collection(rep, rep.scope(), parent_iterator=loop_var)
        elif len(loop_var.scope()[0]) > 0:
            rep = cpp_forward_capture(rep, loop_var, loop_var.scope(), cpp_type=rep.cpp_type(), is_pointer=rep.is_pointer(), the_ast=rep.as_ast())
            rep.is_iterable = True
        else:
            # Just need to reset the scope here.
            rep = cpp_forward_capture(rep, loop_var, loop_var.scope(), cpp_type=rep.cpp_type(), is_pointer=rep.is_pointer(), the_ast=rep.as_ast())
        select_ast.rep = rep
        self._result = rep

        # Finally, we should be at the same basic scoping level as we were when we started. We aren't
        # supposed to be going down a loop in here.
        self._gc.set_scope(start_scope)

    def visit_SelectMany(self, node):
        r'''
        Apply the selection function to the base to generate a collection, and then
        loop over that collection.
        '''
        # Make sure the source is around. We have to do this because code generation in this
        # framework is lazy. And if the `selection` function does not use the source, and
        # looking at that source might generate a loop, that loop won't be generated! Ops!
        self.assure_in_loop(node.source)

        # We need to "call" the source with the function. So build up a new
        # call, and then visit it.

        c = ast.Call(func=lambda_unwrap(node.selection), args=[node.source])

        # Get the collection, and then generate the loop over it.
        # It could be that this comes back from something that is already iterating (like a Select statement),
        # in which case we are already looping.
        (c_iter, c_loop)  = self.assure_in_loop(c)

        node.rep = c_iter

    def visit_Where(self, node):
        'Apply a filtering to the current loop.'

        # Make sure we are in a loop
        (c_iter, c_loop) = self.assure_in_loop(node.source)

        # Simulate the filtering call - we want the resulting value to test.
        filter = lambda_unwrap(node.filter)
        c = ast.Call(func=filter, args=[c_iter.as_ast()])
        rep = self.get_rep(c)

        # Create an if statement
        self._gc.add_statement(statement.iftest(rep))

        # Finally, our result is basically what we had for the source. Note that we
        # need to keep the scoping the same for this iterator as our original iterator.
        new_loop_var = cpp_expression(c_iter.as_cpp(), c_loop, self._gc.current_scope(), cpp_type=c_iter.cpp_type(), is_pointer=c_iter.is_pointer())
        new_loop_var.is_iterable = c_iter.is_iterable
        node.rep = new_loop_var

        self._result = new_loop_var

    def visit_First(self, node):
        'We are in a sequence. Take the first element of the sequence and use that for future things.'

        # Make sure we are in a loop.
        (c_iter, c_loop) = self.assure_in_loop(node.source)

        # The First terminal works by protecting the code with a if (first_time) {} block.
        # We need to declare the first_time variable outside the block where the thing we are
        # looping over here is defined. This is a little tricky, so we delegate to another method.
        loop_scope = c_loop.scope()
        outside_block_scope = loop_scope[0][-1]

        # Define the variable to track this outside that block.
        is_first = cpp_variable(unique_name('is_first'), None, cpp_type='bool', initial_value='true')
        outside_block_scope.declare_variable(is_first)

        # Now, as long as is_first is true, we can execute things inside this statement.
        # The trick is putting the if statement in the right place. We need to locate it just one level
        # below where we defined the scope above.
        s = statement.iftest(is_first)
        s.add_statement(statement.set_var(is_first, cpp_constant('false', cpp_type='bool')))

        self._gc.add_statement(s)        

        # Finally, the result of first is the object that we are looping over.
        new_loop_var = copy(c_iter)
        new_loop_var.is_iterable = False
        new_loop_var.set_scope(self._gc.current_scope())

        node.rep = new_loop_var
        self._result = new_loop_var

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

# The following was copied from: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s22.html
def _find(pathname, matchFunc=os.path.isfile):
    for dirname in sys.path:
        candidate = os.path.join(dirname, pathname)
        if matchFunc(candidate):
            return candidate
    raise BaseException("Can't find file %s" % pathname)

def find_file(pathname):
    return _find(pathname)

def find_dir(path):
    return _find(path, matchFunc=os.path.isdir)

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
        ast = aggregate_node_transformer().visit(ast)
        ast = simplify_chained_calls().visit(ast)
        ast = remove_tuple_subscripts().visit(ast)
        ast = find_known_functions().visit(ast)

        # Any C++ custom code needs to be threaded into the ast
        ast = cpp_ast.cpp_ast_finder().visit(ast)

        # And return the modified ast
        return ast

    def evaluate(self, ast):
        r"""
        Evaluate the ast over the file that we have been asked to run over
        """

        # Visit the AST to generate the code structure and find out what the
        # result is going to be.
        qv = query_ast_visitor()
        result_rep = qv.get_rep(ast)
        return self.get_result(qv, result_rep)

    def get_result(self, qv, result_rep):
        # Emit the C++ code into our dictionaries to be used in template generation below.
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

            # Next, copy over and fill the template files that will control the xAOD running.
            # Assume they are located relative to the python include path.
            template_dir = find_dir("./R21Code")
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

            # Now use docker to run this mess
            docker_cmd = "docker run --rm -v {0}:/scripts -v {0}:/results -v {1}:/data  atlas/analysisbase:21.2.62 /scripts/runner.sh".format(
                local_run_dir, datafile_dir)
            
            if dump_running_log:
                r = subprocess.call(docker_cmd, stderr=subprocess.STDOUT, shell=False)
                print ("Result of run: {0}".format(r))
            else:
                r = subprocess.call(docker_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=False)
            if r != 0:
                raise BaseException("Docker command failed with error {0}".format(r))

            if dump_cpp:
                os.system("type " + os.path.join(local_run_dir, "query.cxx"))

            # Extract the result.
            if type(result_rep) not in result_handlers:
                raise BaseException('Do not know how to process result of type {0}.'.format(type(result_rep).__name__))
            return result_handlers[type(result_rep)](result_rep, local_run_dir)
