# Tests for ast_util.py

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Now the real test code starts.
from clientlib.ast_util import lambda_is_identity, lambda_test, lambda_is_true, lambda_unwrap, lambda_body_replace
import ast

# Identity
def test_identity_is():
    assert lambda_is_identity(ast.parse('lambda x: x')) == True
test_identity_is()

def test_identity_isnot_body():
    assert lambda_is_identity(ast.parse('lambda x: x+1')) == False

def test_identity_isnot_args():
    assert lambda_is_identity(ast.parse('lambda x,y: x')) == False

def test_identity_isnot_body_var():
    assert lambda_is_identity(ast.parse('lambda x: x1')) == False

# Is this a lambda?
def test_lambda_test_expression():
    assert lambda_test(ast.parse("x")) == False

def test_lambda_test_lambda_module():
    assert lambda_test(ast.parse('lambda x: x')) == True

def test_lambda_test_raw_lambda():
    rl = ast.parse('lambda x: x').body[0].value
    assert lambda_test(rl) == True

# Is this lambda always returning true?
def test_lambda_is_true_yes():
    assert lambda_is_true(ast.parse("lambda x: True")) == True
test_lambda_is_true_yes()

def test_lambda_is_true_no():
    assert lambda_is_true(ast.parse("lambda x: False")) == False

def test_lambda_is_true_expression():
    assert lambda_is_true(ast.parse("lambda x: x")) == False

# Lambda unwrap
def test_unwrap_bad_lambda():
    try:
        lambda_unwrap(ast.parse('x+1'))
        assert False
    except:
        pass

# Lambda body replace
def test_lambda_replace_simple():
    t = ast.parse("lambda b: b+1")
    b = ast.parse("2*b").body[0].value
    expected = ast.parse("lambda b: 2*b")

    assert ast.dump(expected) == ast.dump(lambda_body_replace(t, b))

def test_lambda_replace_simple_unwrapped():
    t = lambda_unwrap(ast.parse("lambda b: b+1"))
    b = ast.parse("2*b").body[0].value
    expected = lambda_unwrap(ast.parse("lambda b: 2*b"))

    assert ast.dump(expected) == ast.dump(lambda_body_replace(t, b))

