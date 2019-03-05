# Run the training

# Get the import working from local files
from clientlib.DataSets import EventDataSet
import xAODlib.Jets
import xAODlib.EventCollections

# The input file we are going to use to do the training
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")

# Turn into an event stream that is known by ATLAS.
events = f.AsATLASEvents()

# # Next, get the jet pT's, which we want to look at.
# event_info = events.Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))')
# per_jet = event_info.SelectMany('lambda e: e[1].SelectMany(lambda j: (e[0], j))')
# jet_dump = per_jet.Select('lambda j: j[0].runNumber()')
# training_df = jet_dump.AsPandasDF(['RunNumber']).value()
# jet_pts = events.SelectMany(
#     'lambda e: e.Jets("AntiKt4EMTopoJets")').Select("lambda j: (j.pt(), j.eta(), j.getMomentFloat('Width'))")

# # Save it to a dataframe
# training_df = jet_pts.AsPandasDF(columns=['JetPt', 'JetEta', 'JetWidth']).value()
training_df = events.Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
    .Select('lambda e1: ((e1[0].runNumber(), e1[0].eventNumber()))') \
    .Select('lambda e2: e2[0]') \
    .AsPandasDF(columns=['RunNumber']).value()

# Following works, but is commented out for now till we can integrate it above. Just
# for show, in short.
# track_pts = events.SelectMany(
#      'lambda e: e.Tracks("InDetTrackParticles")').Select("lambda t: (t.pt(), t.eta())")

# # Save it to a dataframe
# training_df = track_pts.AsPandasDF(columns=['TrackPt', 'TrackEta']).value()

print(training_df)
