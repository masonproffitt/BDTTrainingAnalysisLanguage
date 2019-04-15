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
import ast
from clientlib.ObjectStream import ObjectStream
from xAODlib.atlas_xaod_executor import atlas_xaod_executor
from xAODlib.util_scope import top_level_scope
from cpplib.cpp_representation import cpp_variable, cpp_sequence
from clientlib.DataSets import EventDataSet
from math import sin


class dummy_executor(atlas_xaod_executor):
    'Override the docker part of the execution engine'
    def __init__ (self):
        self.QueryVisitor = None
        self.ResultRep = None

    def get_result(self, q_visitor, result_rep):
        'Got the result. Cache for use in tests'
        self.QueryVisitor = q_visitor
        self.ResultRep = result_rep
        return self

# Define a dataset we can use
class test_stream(ast.AST):
    def __init__ (self):
        iter = cpp_variable("bogus-do-not-use", scope=top_level_scope(), cpp_type=None)
        self.rep = cpp_sequence(iter, iter)
        self.rep._ast = self # So that we get used properly when passed on.

    def get_executor(self):
        return dummy_executor()

class dummy_emitter:
    def __init__ (self):
        self.Lines = []
        self._indent_level = 0

    def add_line (self, l):
        if l == '}':
            self._indent_level -= 1

        self.Lines += [
            "{0}{1}".format("  " * self._indent_level, l)]

        if l == '{':
            self._indent_level += 1

    def process (self, func):
        func(self)
        return self
        
class MyEventStream(ObjectStream):
    def __init__ (self):
        ObjectStream.__init__(self, test_stream())

def get_lines_of_code(executor):
    'Return all lines of code'
    qv = executor.QueryVisitor
    d = dummy_emitter()
    qv.emit_query(d)
    return d.Lines

def find_line_with(text, lines, throw_if_not_found = True):
    'Find the first line with the text. Return its index, zero based'
    for index, l in enumerate(lines):
        if text in l:
            return index
    if throw_if_not_found:
        raise BaseException("Unable to find text '{0}' in any lines in text output".format(text))
    return -1

def find_line_numbers_with(text, lines):
    return [index for index,l in enumerate(lines) if text in l]

def print_lines(lines):
    for l in lines:
        print(l)

def find_next_closing_bracket(lines):
    'Find the next closing bracket. If there is an opening one, then track through to the matching closing one.'
    depth = 0
    for index, l in enumerate(lines):
        if l.strip() == "{":
            depth += 1
        if l.strip() == "}":
            depth -= 1
            if depth < 0:
                return index
    return -1

def find_open_blocks(lines):
    'Search through and record the lines before a {. If a { is closed, then remove that lines'
    stack = []
    last_line_seen = 'xxx-xxx-xxx'
    for l in lines:
        if l.strip() == '{':
            stack += [last_line_seen]
        elif l.strip() == '}':
            stack = stack[:-1]
        last_line_seen = l
    return stack

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

def test_first_jet_in_event():
    MyEventStream() \
        .Select('lambda e: e.Jets("bogus").Select(lambda j: j.pt()).First()') \
        .AsROOTFile('dude') \
        .value()

def test_count_after_single_sequence():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: j.pt()).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_with_filter():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: j.pt()).Where(lambda jpt: jpt>10.0).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("if", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_double_sequence():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").SelectMany(lambda j: e.Tracks("InnerTracks")).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_double_sequence_with_filter():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").SelectMany(lambda j: e.Tracks("InnerTracks").Where(lambda t: t.pt()>10.0)).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("if", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 1 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence_unwound():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).SelectMany(lambda ts: ts).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    assert 2 == ["for" in l for l in lines].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_count_after_single_sequence_of_sequence_with_useless_where():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks").Where(lambda pt: pt > 10.0)).Count()') \
        .AsROOTFile('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    # Make sure there is just one for loop in here.
    l_increment = find_line_with('+1', lines)
    block_headers = find_open_blocks(lines[:l_increment])
    assert 1 == ["for" in l for l in block_headers].count(True)
    # Make sure the +1 happens after the for, and before another } bracket.
    num_for = find_line_with("for", lines)
    num_inc = find_line_with("+1", lines[num_for:])
    num_close = find_next_closing_bracket(lines[num_for:])
    assert num_close > num_inc

def test_first_can_be_iterable_after_where():
    # This was found while trying to generate a tuple for some training, below, simplified.
    # The problem was that First() always returned something you weren't allowed to iterate over. Which is not what we want here.
    MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
        .AsROOTFile('dude') \
        .value()

def test_first_can_be_iterable():
    # Make sure a First() here gets called back correctly and generated.
    MyEventStream() \
        .Select('lambda e: e.Jets("AllMyJets").Select(lambda j: e.Tracks("InnerTracks")).First().Count()') \
        .AsROOTFile('dude') \
        .value()

def test_first_after_selectmany():
    MyEventStream() \
        .Select('lambda e: e.Jets("jets").SelectMany(lambda j: e.Tracks("InnerTracks")).First()') \
        .AsROOTFile('dude') \
        .value()

def test_first_after_where():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Where(lambda j: j.pt() > 10).First().pt()') \
        .AsPandasDF('FirstJetPt') \
        .value()

def test_first_object_in_each_event():
    # Part of testing that First puts its outer settings in the right place.
    # This also tests First on a collection of objects that hasn't been pulled a part
    # in a select.
    MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
        .AsPandasDF('FirstJetPt') \
        .value()

def test_Aggregate_per_jet():
    MyEventStream() \
        .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()).Count()") \
        .AsROOTFile("n_jets") \
        .value()

def test_Aggregate_not_inital_const_SUM():
    MyEventStream() \
        .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j: j.pt()/1000).Sum()") \
        .AsROOTFile("n_jets") \
        .value()

def test_First_Of_Select_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .AsPandasDF('FirstJetPt') \
        .value()
    # Check to see if there mention of push_back anywhere.
    lines = get_lines_of_code(r)
    print_lines(lines)
    assert all("push_back" not in l for l in lines)
    l_fill = find_line_with("Fill()", lines)
    active_blocks = find_open_blocks(lines[:l_fill])
    assert 0==[(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_set = find_line_with("_FirstJetPt", lines)
    active_blocks = find_open_blocks(lines[:l_set])
    assert 3==[(("for" in a) or ("if" in a)) for a in active_blocks].count(True)
    l_true = find_line_with("(true)", lines)
    active_blocks = find_open_blocks(lines[:l_true])
    assert 0==[(("for" in a) or ("if" in a)) for a in active_blocks].count(True)

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

def test_First_Of_Select_After_Where_is_in_right_place():
    # Make sure that we have the "First" predicate after if Where's if statement.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .AsPandasDF('FirstJetPt') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    l = find_line_with(">10.0", lines)
    # Look for the "false" that First uses to remember it has gone by one.
    assert find_line_with("false", lines[l:], throw_if_not_found=False) > 0

def test_First_selects_collection_count():
    # Make sure that we have the "First" predicate after if Where's if statement.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
        .AsPandasDF('TrackCount') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    l = find_line_numbers_with("for", lines)
    assert 2==len(l)

def test_sequence_with_where_first():
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
        .AsPandasDF('dude') \
        .value()
    lines = get_lines_of_code(r)
    print_lines(lines)
    l_first = find_line_numbers_with("if (is_first", lines)
    assert 1 == len(l_first)
    active_blocks = find_open_blocks(lines[:l_first[0]])
    assert 1==["for" in a for a in active_blocks].count(True)
    l_agg = find_line_with("+1", lines)
    active_blocks = find_open_blocks(lines[:l_agg])
    assert 1==[">1000" in a for a in active_blocks].count(True)
