# Use this node in the ast when you want to add some custom C++
#
# This is one mechanism to allow for a leaky abstraction.
import ast
from cpplib.cpp_representation import cpp_variable
from cpplib.cpp_vars import unique_name
import xAODlib.statement as statements

# The list of methods and the re-write functions for them. Each rewrite function
# is called with the Call node, which includes arguments, names, etc. It should return
# None or a cpp_ast.
method_names = {}

class CPPCodeValue (ast.AST):
    r'''
    Represents a C++ bit of code that returns a value. Like a function call or a member call.
    Use the be-fore the wire visit phase of processing to look for a pattern that needs
    to generate AST code, like a method call. Then place this AST in place of the function.
    The back-end will then do the rendering useing the information included below.
    '''

    def __init__(self):
        # Files that need to be included at the top of the generated C++ file
        self.include_files = []

        # Code that is run once at the start of each "event"
        self.initialization_code = []

        # Code that is run when the particular bit of code needs to be invoked (e.g. in the middle of a hot loop).
        # This is invoked in its own scope (between "{" and "}") so there are no variable collisions.
        self.running_code = []

        # Replacements - in all the code replace the keys with the values. This is so arguments can be pasted in directly.
        # "obj" is specially - if this is a method call, it represents the object that is getting called against.
        self.replacements = {}

        # Special replacement if this is a method call. A tuple. THe first item is the string to be replaced in the
        # code. The second is the name against which we should be making the call (e.g. if j is the current jet variable,
        # the tuple might be ("obj", "j")).
        self.replacement_instance_obj = None

        # A string representing the result value. This must be a simple variable.
        self.result = None

        # We have no further fields for the ast machinery to explore, so this is empty for now.
        self.fields=[]

class cpp_ast_finder(ast.NodeTransformer):
    r'''
    Look through the complete ast and replace method calls that are to a C++ plug in with a c++ ast
    node.
    '''

    def visit_Call(self, node):
        r'''
        Looking for a member call of a particular name. We rewrite that as
        another name.
        WARNING: currently the namespace is global, so the parent type doesn't matter!
        '''

        # Examine the func to see if this is a member call.
        func = node.func
        if type(func.value) is not ast.Name:
            return node

        # Next, get the name and see if we can find it somewhere.
        if func.attr in method_names:
            cpp_call_ast = method_names[func.attr](node)
            if cpp_call_ast is not None:
                return cpp_call_ast

        return node

def process_ast_node(visitor, gc, current_loop_value, call_node):
    r'''Inject the proper code into the output stream to deal with this C++ code.
    
    We expect this to be run at the back-end.

    visitor - The node visitor that is converting the code into C++
    gc - the generated code object that we fill with actual code
    current_loop_variable - the thing we are currently iterating over
    call_node - a Call ast node, with func being a CPPCodeValue.

    Result:
    representation - A value that represents the output
    '''

    # We write everything into a new scope to prevent conflicts. So we have to declare the result ahead of time.
    result_rep = cpp_variable(unique_name("cppResult"))
    gc.declare_variable("float", result_rep.name())

    # Build the dictionary for replacement
    cpp_ast_node = call_node.func
    repl_list = []
    if cpp_ast_node.replacement_instance_obj is not None:
        repl_list += [(cpp_ast_node.replacement_instance_obj[0], visitor.resolve_id(cpp_ast_node.replacement_instance_obj[1]).rep.name())]
    for src,dest in cpp_ast_node.replacements.items():
        if type(dest) is str:
            dest = '"' + dest + '"'
        repl_list += [(src, dest)]

    # Emit the statements.
    blk = statements.block()
    visitor._gc.add_statement(blk)

    for s in cpp_ast_node.running_code:
        l = s
        for src,dest in repl_list:
            l = l.replace(src, dest)            
        blk.add_statement(statements.arbitrary_statement(l))

    # Set the result and close the scope
    blk.add_statement(statements.set_var(result_rep.name(), cpp_ast_node.result))
    gc.pop_scope()

    return result_rep
