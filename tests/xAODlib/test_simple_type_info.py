# Test the simple type information system.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
# Code to do the testing starts here.
from tests.xAODlib.utils_for_testing import *

def test_cant_call_double():
    try: 
        MyEventStream() \
            .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt().eta()).Sum()") \
            .AsROOTFile("n_jets") \
            .value()
    except BaseException as e:
        if "Unable to call method 'eta' on type 'double'" not in str(e):
            raise e from None
        assert "Unable to call method 'eta' on type 'double'" in str(e)
        return
    # Should never get here!
    assert False
