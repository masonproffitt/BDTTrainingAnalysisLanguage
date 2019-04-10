# Tests for ast_util.py

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Now the real test code starts.
from clientlib.ast_util import lambda_is_identity
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
