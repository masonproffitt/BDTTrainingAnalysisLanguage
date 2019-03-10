# The representation, in C++ code, of a particular variable.
# This is an abstract class. Almost everyone is going to have to
# implement one.
#
import xAODlib.statement as statement
import ast

def name_from_rep(rep):
    'Create an ast.Name from a variable representation'
    a = ast.Name(rep.name())
    a.rep = rep
    return a

class cpp_rep_base:
    r'''
    Represents a term or collection in C++ code. Queried to perform certian actions on the C++ term or collection.

    This is an abstract class for the most part. Do not override things that aren't needed - that way the system will
    know when the user tries to do something that they shouldn't have.
    '''

    def as_cpp(self):
        'Return the C++ code to represent whatever we are holding'
        raise BaseException("Subclasses need to implement in for as_cpp")

class cpp_variable(cpp_rep_base):
    r'''
    The representation for a simple variable.
    '''

    def __init__(self, name, is_pointer=False, cpp_type = None):
        self._cpp_name = name
        self._is_pointer = is_pointer
        self._cpp_type = cpp_type

    def name(self):
        return self._cpp_name

    def as_cpp(self):
        return self._cpp_name

    def is_pointer(self):
        return self._is_pointer

    def cpp_type(self):
        return self._cpp_type

class cpp_expression(cpp_rep_base):
    r'''
    Represents a small bit of C++ code that is an expression. For example "a+b". It does not hold full
    statements.
    '''
    def __init__(self, expr, cpp_type=None):
        self._expr = expr
        self._cpp_type = cpp_type

    def as_cpp(self):
        return self._expr

class cpp_collection(cpp_variable):
    r'''
    The representation for a collection. Something that can be iterated over.
    '''

    def __init__(self, name, is_pointer=False, cpp_type=None):
        r'''Remember the C++ name of this variable

        name - The name of the variable we are going to save here
        is_pointer - do we need to de-ref it to access it?
        '''
        cpp_variable.__init__(self, name, is_pointer, cpp_type=cpp_type)

    def loop_over_collection(self, gc):
        r'''
        Generate a loop over the collection

        gc - generated_code object to store code in

        returns:

        obj - term containing the object that is the loop variable
        '''

        # Create the var we are going to iterate over, and figure out how to reference
        # What we are doing.
        v = cpp_variable("jet", is_pointer=True)
        c_ref = ("*" + self.name()) if self.is_pointer() else self.name()

        # Finally, the actual loop statement.
        gc.add_statement(statement.loop(c_ref, v.name()))

        # and that iterating variable is the rep
        return v
