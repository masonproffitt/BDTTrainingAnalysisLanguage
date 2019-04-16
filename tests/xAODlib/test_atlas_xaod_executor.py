# Test of the executor
# Eventually this will probably have to be split into several bits, as this is quite
# a bit of code to test. But for now...
# WARNING: this code can be a bit fragile - as it is relying on how the C++ code is generated, and that
# can change w/out there being any functional change... But these tests run in miliseconds compared to the actual running
# against data where a single test can take 30 seconds.

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Code to do the testing starts here.
from math import sin
from tests.xAODlib.utils_for_testing import *

##############################
# Tests that just make sure we can generate everything without a crash.

def test_per_event_item():
    r=MyEventStream().Select('lambda e: e.EventInfo("EventInfo").runNumber()').AsROOTFile('RunNumber').value()
    vs = r.QueryVisitor._gc._class_vars
    assert 1 == len(vs)
    assert "double" == str(vs[0].cpp_type())

def test_func_sin_call():
    MyEventStream().Select('lambda e: sin(e.EventInfo("EventInfo").runNumber())').AsROOTFile('RunNumber').value()

def test_per_jet_item_as_call():
    MyEventStream().SelectMany('lambda e: e.Jets("bogus")').Select('lambda j: j.pt()').AsROOTFile('dude').value()

def test_Select_is_an_array_with_where():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0)') \
        .AsPandasDF('JetPts') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_is_an_array():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt())') \
        .AsPandasDF('JetPts') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 1==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_is_not_an_array():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt())') \
        .AsPandasDF('JetPts') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1==["for" in a for a in active_blocks].count(True)

def test_Select_Multiple_arrays():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: (e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0),e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.eta()))') \
        .AsPandasDF(('JetPts','JetEta')) \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 2==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_Multiple_arrays_2_step():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets")') \
        .Select('lambda jets: (jets.Select(lambda j: j.pt()/1000.0),jets.Select(lambda j: j.eta()))') \
        .AsPandasDF(('JetPts','JetEta')) \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_push_back = find_line_numbers_with("push_back", lines)
    assert all([len([l for l in find_open_blocks(lines[:pb]) if "for" in l])==1 for pb in l_push_back])
    assert 2==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 0==["for" in a for a in active_blocks].count(True)

def test_Select_of_2D_array_fails():
    # The following statement should be a straight sequence, not an array.
    try:
        MyEventStream() \
            .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: (j.pt()/1000.0, j.eta()))') \
            .AsPandasDF(['JetInfo']) \
            .value()
    except BaseException as e:
        assert "Nested data structures" in str(e)

def test_SelectMany_of_tuple_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
            .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: (j.pt()/1000.0, j.eta()))') \
            .AsPandasDF(['JetPts', 'JetEta']) \
            .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert 0==["push_back" in l for l in lines].count(True)
    l_push_back = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_push_back])
    assert 1==["for" in a for a in active_blocks].count(True)
