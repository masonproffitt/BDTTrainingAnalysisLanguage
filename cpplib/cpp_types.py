# Simple type system to help reason about types as they go through the system.

class terminal:
    'Represents something we cannot see inside, like float, or int, or bool'
    def __init__ (self, t, is_pointer = False):
        '''
        Initialize a terminal type

        t:      The type as a string (valid in C++)
        '''
        self._type = t
        self._is_pointer = is_pointer

    def __str__(self):
        return self._type

    def is_pointer(self):
        return self._is_pointer

class collection:
    'Represents a collection/list/vector of the same type'
    def __init__ (self, t):
        '''
        Initialize a collection type.

        t:      The type of each element in the collection
        '''
        self._element_type = t

    def __str__(self):
        return "vector<" + self._element_type + ">"

    def element_type(self):
        return self._element_type

class tuple:
    'Represents a value which is a collection of other types'
    def __init__ (self, type_list):
        '''
        Initialize a type list. The value consists of `len(type_list)` items, each
        of the type held inside type_lits.

        type_list:      tuple,etc., that we can iterate over to get the types.
        '''
        self._type_list = type_list

    def __str__(self):
        return "(" + ','.join(self._type_list) + ")"