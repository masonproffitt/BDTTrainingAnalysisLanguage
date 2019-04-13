# Test of the executor
# Eventually this will probably have to be split into several bits, as this is quite
# a bit of code to test. But for now...

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Code to do the testing starts here.
import ast
from clientlib.ObjectStream import ObjectStream
from xAODlib.atlas_xaod_executor import atlas_xaod_executor
from cpplib.cpp_representation import cpp_variable
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
        self.rep = cpp_variable("bogus-do-not-use", scope=None)
        self.rep.is_iterable = True # No need to build up a new loop - implied!
        self.rep._ast = self # So that we get used properly when passed on.

    def get_executor(self):
        return dummy_executor()

class MyEventStream(ObjectStream):
    def __init__ (self):
        ObjectStream.__init__(self, test_stream())

##############################
# Tests that just make sure we can generate everything without a crash.

def test_per_event_item():
    MyEventStream().Select('lambda e: e.EventInfo("EventInfo").runNumber()').AsROOTFile('RunNumber').value()

def test_func_sin_call():
    MyEventStream().Select('lambda e: sin(e.EventInfo("EventInfo").runNumber())').AsROOTFile('RunNumber').value()

def test_per_jet_item_as_call():
    MyEventStream().SelectMany('lambda e: e.Jets("bogus")').Select('lambda j: j.pt()').AsROOTFile('dude').value()

def test_first_jet_in_event():
    MyEventStream() \
        .Select('lambda e: e.Jets("bogus").Select(lambda j: j.pt()).First()') \
        .AsROOTFile('dude') \
        .value()

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

def test_First_Of_Select_is_not_array():
    # The following statement should be a straight sequence, not an array.
    r = MyEventStream() \
        .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
        .AsPandasDF('FirstJetPt') \
        .value()
    print (r)
    # Check there is no push_back
    assert True==False