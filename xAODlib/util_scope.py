# Scope related utilities
# see https://stackoverflow.com/questions/33533148/how-do-i-specify-that-the-return-type-of-a-method-is-the-same-as-the-class-itsel
# for info on this next line. Already looking forward to python 4...
from __future__ import annotations
import copy

def top_level_scope():
    '''
    Returns a top level scope. Basically, the class level.
    '''
    return gc_scope_top_level()

class gc_scope_top_level:
    def is_top_level(self):
        return True

class gc_scope:
    'Internal class to track the scope of a statement.'
    def __init__(self, scope_stack):
        self._scope_stack = copy.copy(scope_stack)

    def __getitem__(self, key: int) -> gc_scope:
        '''
        Return a new scope, some number "up" from where we are now. This uses standard
        array slicing in python. If you do 0 you'll get back the top level. If you do -1
        you will get back everything but the last thing. -2 last two thigns, etc.
        '''
        if type(key) is not int:
            raise BaseException("Key must be an integer")

        if len(self._scope_stack[:key]) == 0:
            raise BaseException("Winding up at the top level scope is not yet supported")

        return gc_scope(self._scope_stack[:key])

    def frame_statements(self, key):
        'Return the nth frame block. -1 means the last one, 0 means the deepest (top) one.'
        return self._scope_stack[key]

    def declare_variable(self, var) -> None:
        'Declare a class at the scope level'
        self._scope_stack[-1].declare_variable(var)

    def starts_with(self, c: gc_scope):
        '''
        Return true if the scope c matches the first part of our scope. False otherwise.
        '''
        if c.is_top_level() and self.is_top_level():
            return True
        if c.is_top_level():
            return True
        if self.is_top_level():
            return False
            
        if len(c._scope_stack) > len(self._scope_stack):
            return False
        
        return all([a is b for a,b in zip(self._scope_stack, c._scope_stack[:len(self._scope_stack)])])

    def is_top_level(self):
        return False

def scope_is_deeper(s1, s2):
    '''Return true if scope `s2` is deeper than scope `s`.
    
    s1 - returned from the `current_scope()` on `generated_code`.
    s2 - a second scope from the same function.

    returns:

    is_deeper - true if scope s2 has more levels than s1.
    throws if for the frames that s1 and s2 have, if they do not match.

    '''
    stack_1 = s1[0]
    stack_2 = s2[0]

    are_same = all(a1 == a2 for a1,a2 in zip(stack_1, stack_2))
    if not are_same:
        raise BaseException("Unable to determine relative scope differences unless the initial part of the scope is the same!")

    return len(stack_1) < len(stack_2)

