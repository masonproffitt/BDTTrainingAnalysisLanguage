# Some simple tests to make sure call stack works right.
from clientlib.call_stack import argument_stack, stack_frame

def test_name_not_found():
    c = argument_stack()
    assert 'a' == c.lookup_name('a')

def test_name_found():
    c = argument_stack()
    c.define_name('a', 'dude')
    assert 'dude' == c.lookup_name('a')

def test_name_in_level_up():
    c = argument_stack()
    c.define_name('a', 'dude')
    c.push_stack_frame()
    assert 'dude' == c.lookup_name('a')

def test_name_in_level_gone():
    c = argument_stack()
    c.push_stack_frame()
    c.define_name('a', 'dude')
    c.pop_stack_frame()
    assert 'a' == c.lookup_name('a')

def test_name_is_hidden():
    c = argument_stack()
    c.define_name('a', 'dude1')
    c.push_stack_frame()
    c.define_name('a', 'dude2')
    assert 'dude2' == c.lookup_name('a')
    c.pop_stack_frame()
    assert 'dude1' == c.lookup_name('a')

def test_with_class():
    c = argument_stack()
    with stack_frame(c):
        c.define_name('a', 'dude')
        assert 'dude' == c.lookup_name('a')
    assert 'a' == c.lookup_name('a')

def test_default_return():
    c = argument_stack()
    assert 'dude' == c.lookup_name('a', default='dude')