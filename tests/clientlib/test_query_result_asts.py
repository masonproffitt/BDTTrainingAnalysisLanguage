# Some quick tests for building the asts

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Code to do the testing starts here.
from clientlib.query_result_asts import resultTTree

def test_TTree_columnNames_as_tuple():
    r = resultTTree(None, ('hi', 'here'))
    assert 2 == len(r.column_names)

def test_TTree_columnNames_as_string():
    r = resultTTree(None, 'hi')
    assert 1 == len(r.column_names)
