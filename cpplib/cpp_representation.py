# The representation, in C++ code, of a particular variable.
# This is an abstract class. Almost everyone is going to have to
# implement one.
#
import xAODlib.statement as statement
from cpplib.cpp_vars import unique_name
import ast

class cpp_rep_base:
    r'''
    Represents a term or collection in C++ code. Queried to perform certian actions on the C++ term or collection.

    This is an abstract class for the most part. Do not override things that aren't needed - that way the system will
    know when the user tries to do something that they shouldn't have.
    '''
    def __init__(self, scope, is_pointer = False, cpp_type=None):
        # Set to true when we represent an item in an interable type.
        self.is_iterable = False
        self._ast = None
        self._scope = scope
        self._is_pointer = is_pointer
        self._cpp_type = cpp_type

    def is_pointer(self):
        return self._is_pointer

    def as_cpp(self):
        'Return the C++ code to represent whatever we are holding'
        raise BaseException("Subclasses need to implement in for as_cpp")

    def as_ast(self):
        'Return a python AST for this representation'
        if not self._ast:
            self.make_ast()
        return self._ast
    
    def make_ast(self):
        'Create and fill the _ast variable with the ast for this rep'
        raise BaseException("Internal Error: Subclasses need to implement this in as_ast")

    def scope(self):
        'Return the scope at which this representation was defined'
        return self._scope

    def set_scope(self, s):
        'Change the scope of this variable to something new.'
        self._scope = s

    def cpp_type(self):
        return self._cpp_type

class cpp_variable(cpp_rep_base):
    r'''
    The representation for a simple variable.
    '''

    def __init__(self, name, scope, is_pointer=False, cpp_type = None, initial_value = None):
        '''
        Create a new variable

        name - C++ name of the variable
        scope - Scope at which this variable is being defined
        is_pointer - True if we need to use -> to dereference it
        cpp_type - tye type of the variable, or implied (somehow)
        initial_value - if set, then it will be used to declare the variable and initially set it.
        '''
        cpp_rep_base.__init__(self, scope, is_pointer=is_pointer, cpp_type=cpp_type)
        self._cpp_name = name
        self._ast = None
        self._initial_value = initial_value

    def name(self):
        return self._cpp_name

    def initial_value(self):
        return self._initial_value

    def as_cpp(self):
        return self._cpp_name

    def make_ast(self):
        self._ast = ast.Name(self.as_cpp(), ast.Load())
        self._ast.rep = self

    def scope_of_iter_definition(self):
        'Return the scope where this variable was defined'
        return self.scope()

    def find_best_iterator(self):
        'We are the best possible iterator!'
        if not self.is_iterable:
            raise BaseException('Attempt to find the iterator for a non-iterating variable')
        return self

class cpp_tuple(cpp_rep_base):
    r'''
    Sometimes we need to carry around a tuple. Unfortunately, we can't "add" items onto a regular
    python tuple (like is_iterable, etc.). So we have to have this special wrapper.
    '''
    def __init__ (self, t, scope):
        cpp_rep_base.__init__(self, scope)
        self._tuple = t
    
    def tup(self):
        return self._tuple

    def as_cpp(self):
        'Return a dummy - this should never actually be used'
        return 'tuple-rendering-bogus'

class cpp_constant(cpp_rep_base):
    r'''
    Represents a constant
    '''
    def __init__(self, val, cpp_type = None):
        cpp_rep_base.__init__(self, None, is_pointer=False, cpp_type=cpp_type)
        self._val = val

    def as_cpp(self):
        return self._val
class cpp_expression(cpp_rep_base):
    r'''
    Represents a small bit of C++ code that is an expression. For example "a+b". It does not hold full
    statements.

    TODO: Does not yet automatically make an ast for this guy.
    '''
    def __init__(self, expr, iterator_var, scope, cpp_type=None, is_pointer = False, the_ast = None):
        cpp_rep_base.__init__(self, scope, is_pointer=is_pointer, cpp_type=cpp_type)
        self._expr = expr
        self._ast = the_ast
        self._iterator = iterator_var #.get_iterator_var() if iterator_var is not None else None

    def as_cpp(self):
        return self._expr

    def find_best_iterator(self):
        'Internal method to get the iterator'
        if self._iterator is None:
            return None
        if type(self._iterator) is not list:
            return self._iterator.find_best_iterator() 

        # Now we have choices. So, lets get all of them we can.
        c = [b for b in [a.find_best_iterator() for a in self._iterator if hasattr(a, 'find_best_iterator')] if b is not None]
        if len(c) > 1:
            raise BaseException("Can't decide what iterator is best! Internal error!")
        return c[0]

    def scope_of_iter_definition(self):
        'Return the scope where this variable was defined'
        i = self.find_best_iterator()
        return i.scope_of_iter_definition() if i is not None else self.scope()
        
    def make_ast(self):
        self._ast = ast.Name(self.as_cpp(), ast.Load())
        self._ast.rep = self

class cpp_collection(cpp_variable):
    r'''
    The representation for a collection. Something that can be iterated over using
    the standard for loop code.
    '''

    def __init__(self, name, scope, is_pointer=False, cpp_type=None):
        r'''Remember the C++ name of this variable

        name - The name of the variable we are going to save here
        is_pointer - do we need to de-ref it to access it?
        '''
        cpp_variable.__init__(self, name, scope, is_pointer=is_pointer, cpp_type=cpp_type)

    def loop_over_collection(self, gc):
        r'''
        Generate a loop over the collection

        gc - generated_code object to store code in

        returns:

        obj - term containing the object that is the loop variable
        '''

        # Create the var we are going to iterate over, and figure out how to reference
        # What we are doing.
        v = cpp_variable(unique_name("i_obj"), scope = None, is_pointer=True)
        v.is_iterable = True
        c_ref = ("*" + self.name()) if self.is_pointer() else self.name()

        # Finally, the actual loop statement.
        gc.add_statement(statement.loop(c_ref, v.name()))
        v.set_scope(gc.current_scope())

        # and that iterating variable is the rep
        return v

class cpp_iterator_over_collection(cpp_variable):
    r'''
    Special case used to cache an iterator that is at least two levesl down. In short, it is
    an iterator over a collection of collections. These are generated when a Select statement
    returns collection (rather than a single item).
    '''
    def __init__(self, iter, scope):
        '''
        Create an iterator over a collection.

        iter - The iterator cpp_variable (or expression or whatever)
        scope - Scope where this is first valid as something like this.
        '''
        cpp_variable.__init__(self, iter.as_cpp(), scope)
        self._iter = iter

    def iter(self):
        return self._iter

    def loop_over_collection(self, gc):
        'Loop over this iterator.'
        # Unwrap one level
        return self._iter

    def scope_of_iter_definition(self):
        'Return the scope where this variable was defined'
        return self._iter.scope_of_iter_definition()
