# Write out a flat ROOT file that can be used to look for Z->ee and Z->mumu
from clientlib.DataSets import EventDataSet
from cpplib.math_utils import DeltaR
import cpplib.cpp_types as ctyp

class track_columns:
    'Helper method because syntax is not great yet'
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

# Track basic event info, jets, and LLP particles.
# TODO: Sort out which is the proper met
event_info = events \
    .Select(r'''lambda e: (
        e.EventInfo('EventInfo'),
        e.Jets('AntiKt4EMTopoJets'),
        e.TruthParticles('TruthParticles').Where(lambda tp1: abs(tp1.pdgId()) == 11 or abs(tp1.pdgId()) == 13),
        e.MissingET('MET_Core_AntiKt4EMTopo').First(),
        e.Electrons("Electrons"),
        e.Muons("Muons"),
        )
    ''')

# Build us a list of columns
tc = track_columns()
tc.add_col('RunNumber', 'ji[0].runNumber()')
tc.add_col('EventNumber', 'ji[0].eventNumber()')

tc.add_col('jet_pt', 'ji[1].Select(lambda j: j.pt()/1000.0)')
tc.add_col('jet_eta', 'ji[1].Select(lambda j: j.eta()/1000.0)')
tc.add_col('jet_phi', 'ji[1].Select(lambda j: j.phi()/1000.0)')

# MC info
tc.add_col('mc_id', 'ji[2].Select(lambda mc: mc.pdgId())')
tc.add_col('mc_pt', 'ji[2].Select(lambda mc: mc.pt()/1000.0)')
tc.add_col('mc_eta', 'ji[2].Select(lambda mc: mc.eta())')
tc.add_col('mc_phi', 'ji[2].Select(lambda mc: mc.phi())')

# Electron info
tc.add_col('ele_pt', 'ji[4].Select(lambda e: e.pt()/1000.0)')
tc.add_col('ele_eta', 'ji[4].Select(lambda e: e.eta()/1000.0)')
tc.add_col('ele_phi', 'ji[4].Select(lambda e: e.phi()/1000.0)')

# Muon info
tc.add_col('mu_pt', 'ji[5].Select(lambda m: m.pt()/1000.0)')
tc.add_col('mu_eta', 'ji[5].Select(lambda m: m.eta())')
tc.add_col('mu_phi', 'ji[5].Select(lambda m: m.phi())')

# MET
tc.add_col("met_met", 'ji[3].met()/1000.0')

# Most of the mlp stuff is going to come from a bunch of jet moments.
# TODO: Add cut on clean LLP jet
tuple_data = event_info \
    .Select('lambda ji: ' + tc.gen_tuple())

# Put it all together and turn it into a set of ROOT files (for now):
ds = tuple_data \
    .AsROOTFile(tc.col_names) \
    .value()

print (ds)