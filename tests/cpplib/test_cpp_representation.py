# Test the cpp representations. These objects are quite simple, so there
# aren't that many tests. Mostly when bugs are found something gets added here.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

from cpplib.cpp_representation import cpp_expression

def test_expression_pointer_decl():
    e1 = cpp_expression("dude", None, None)
    assert False == e1.is_pointer()

    e2 = cpp_expression("dude", None, None, is_pointer = False)
    assert False == e2.is_pointer()

    e3 = cpp_expression("dude", None, None, is_pointer = True)
    assert True == e3.is_pointer()
