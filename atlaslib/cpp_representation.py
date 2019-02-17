# The representation, in C++ code, of a particular variable.
# This is an abstract class. Almost everyone is going to have to
# implement one.
#
# TODO: lint/pretty up everything.
import atlaslib.statement as statement


class cpp_rep_base:
    r'''
    Represents a term or collection in C++ code. Queried to perform certian actions on the C++ term or collection.

    This is an abstract class for the most part. Do not override things that aren't needed - that way the system will
    know when the user tries to do something that they shouldn't have.
    '''

    def loop_over_collection(self, gen_code):
        '''
        Generate a loop over this collection.
        Assumes: this rep is a collection (otherwise bomb!)

        gen_code - The generated_code item that we can emit the loop on.

        returns:

        loop_rep - A rep that is the C++ variable that allows access to the items of
                   this collection. 
        '''
        raise BaseException("loop_over_collection is not implemented for this type:" + type(self).__name__)
    
    def access_collection(self, gen_code, access_ast):
        '''
        This item has a collection. Access it, using the ast above, and return
        a rep for the collection.
        Assumes: this rep has collections to access. Something representing a float, for example, would not.
        
        gen_code - The generated_code object that we can use to emit C++ code.
        access_ast - a lambda function that when applied to this representation should yield the collection.
                     An error should be thrown if that isn't the case.

        returns:

        collection_rep - A rep that allows code to directly access (loop over, etc) the collection.
        '''
        raise BaseException("access_collection is not implemented for this type:" + type(self).__name__)


class cpp_variable(cpp_rep_base):
    r'''
    The representation for a simple variable.
    '''

    def __init__ (self, name, is_pointer = False):
        self._cpp_name = name
        self._is_pointer = is_pointer

    def name (self):
        return self._cpp_name

    def is_pointer(self):
        return self._is_pointer
        
class cpp_collection(cpp_variable):
    r'''
    The representation for a collection. Something that can be iterated over.
    TODO: Should this be a cpp_variable as well?
    '''

    def __init__(self, name, is_pointer = False):
        r'''Remember the C++ name of this variable

        name - The name of the variable we are going to save here
        is_pointer - do we need to de-ref it to access it?
        '''
        cpp_variable.__init__(self, name, is_pointer)

    def loop_over_collection(self, gc):
        r'''
        Generate a loop over the collection

        gc - generated_code object to store code in

        returns:

        obj - term containing the object
        '''

        # Create the var we are going to iterate over, and figure out how to reference
        # What we are doing.
        v = cpp_variable("jet", is_pointer=True)
        c_ref = ("*" + self.name()) if self.is_pointer() else self.name()

        # Finally, the actual loop statement.
        gc.add_statement(statement.loop(c_ref, v.name()))
