# Write out the training ntuple for doing the r (xy) and z training
from clientlib.DataSets import EventDataSet

class track_columns:
    def __init__(self):
        self.col_names = []
        self.col_expr = []

    def add_col (self, name, expr):
        self.col_names += [name]
        self.col_expr += [expr]

    def col_index(self, name):
        'Return the name of a column'
        for i, n in enumerate(self.col_names):
            if n == name:
                return i
        raise BaseException('Unable to find column "{0}"!'.format(name))

    def gen_tuple(self):
        'Return the tuple string'
        return '({0})'.format(','.join(self.col_expr))


# Use the following datasets as input
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")
events = f.AsATLASEvents()

event_info = events \
    .Select("lambda e: (e.EventInfo('EventInfo'), e.Jets('AntiKt4EMTopoJets'))")
jet_info = event_info \
    .SelectMany('lambda ev: ev[1].Select(lambda j1: (ev[0], j1))')

# Build us a list of columns
tc = track_columns()
tc.add_col('RunNumber', 'ji[0].runNumber()')
tc.add_col('EventNumber', 'ji[0].eventNumber()')

# TODO: jetPt is being placed at the wrong scope.
tc.add_col('JetPt', 'ji[1].pt()/1000.0')
tc.add_col('JetEta', 'ji[1].eta()')

# The basic moments for the layer weights.
# TODO: Add the get attribute that comes back as a vector of double.

# The MC information for the particle
# TODO: Add the mc information

# Most of the mlp stuff is going to come from a bunch of jet moments.
tuple_data = jet_info \
    .Select('lambda ji: ' + tc.gen_tuple()) \
    .Where('lambda jc: jc[{0}] > 40.0'.format(tc.col_index('JetPt')))

# Put it all together and turn it into a set of ROOT files (for now):
ds = tuple_data \
    .AsPandasDF(tc.col_names) \
    .value()

print (ds)