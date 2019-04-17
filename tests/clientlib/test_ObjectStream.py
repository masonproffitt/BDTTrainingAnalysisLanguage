# Simple tests for ObjectStream.


# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

from clientlib.ObjectStream import ObjectStream
import ast


# First set of tests just trying to make sure that parsing of the lambda functions
# happens without errors
def test_lambda_parsing():
    o = ObjectStream(ast.Name(id="dude"))
    o.Select('lambda e: e.Jets')

def test_lambda_with_whitespace():
    o = ObjectStream(ast.Name(id="dude"))
    o.Select('     lambda e: e.Jets     ')

def test_lambda_with_newlines():
    o = ObjectStream(ast.Name(id="dude"))
    j = o.Select(r'''
         lambda e: (e.Jets,
                    e.Tracks)
         ''')
