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

def add_sampling_layer(name, index, tc):
    'Add a column accessing the energy sampling guy'
    # TODO: Add sum on here so we can make this a fraction
    tc.add_col(name, 'ji[1].getAttributeVectorFloat("EnergyPerSampling")[{0}]/1000.0'.format(index))


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

tc.add_col('JetPt', 'ji[1].pt()/1000.0')
tc.add_col('JetEta', 'ji[1].eta()')

# The basic moments for the layer weights.
add_sampling_layer ('EMM_BL0', 0, tc)
add_sampling_layer ('EMM_BL1', 1, tc)
add_sampling_layer ('EMM_BL2', 2, tc)
add_sampling_layer ('EMM_BL3', 3, tc)

add_sampling_layer ('EMM_EL0', 4, tc)
add_sampling_layer ('EMM_EL1', 5, tc)
add_sampling_layer ('EMM_EL2', 6, tc)
add_sampling_layer ('EMM_EL3', 7, tc)

add_sampling_layer ('EH_EL0', 8, tc)
add_sampling_layer ('EH_EL1', 9, tc)
add_sampling_layer ('EH_EL2', 10, tc)
add_sampling_layer ('EH_EL3', 11, tc)

add_sampling_layer ('EH_CBL0', 12, tc)
add_sampling_layer ('EH_CBL1', 13, tc)
add_sampling_layer ('EH_CVL2', 14, tc)

add_sampling_layer ('EH_TGL0', 15, tc)
add_sampling_layer ('EH_TGL1', 16, tc)
add_sampling_layer ('EH_TGL2', 17, tc)

add_sampling_layer ('EH_EBL0', 18, tc)
add_sampling_layer ('EH_EBL1', 19, tc)
add_sampling_layer ('EH_EBL2', 20, tc)

add_sampling_layer ('FC_L0', 21, tc)
add_sampling_layer ('FC_L1', 22, tc)
add_sampling_layer ('FC_L2', 23, tc)

# The MC information for the particle
# TODO: Add the mc information

# Most of the mlp stuff is going to come from a bunch of jet moments.
# TODO: Add cut on clean LLP jet
tuple_data = jet_info \
    .Select('lambda ji: ' + tc.gen_tuple()) \
    .Where('lambda jc: (jc[{0}] > 40.0) and (abs(jc[{1}]) < 2.5)'.format(tc.col_index('JetPt'), tc.col_index('JetEta')))

# Put it all together and turn it into a set of ROOT files (for now):
ds = tuple_data \
    .AsPandasDF(tc.col_names) \
    .value()

print (ds)