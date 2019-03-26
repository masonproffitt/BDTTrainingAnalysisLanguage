# Run the training

# Get the import working from local files
from clientlib.DataSets import EventDataSet

# The input file we are going to use to do the training
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")

# Turn into an event stream that is known by ATLAS.
events = f.AsATLASEvents()

# # Next, get the jet pT's, which we want to look at.
# jet_pts = events.SelectMany(
#     'lambda e: e.Jets("AntiKt4EMTopoJets")').Select("lambda j: (j.pt(), j.eta(), j.getMomentFloat('Width'))")

# # Save it to a dataframe
# training_df = jet_pts.AsPandasDF(columns=['JetPt', 'JetEta', 'JetWidth']).value()
# training_df = events.Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1]') \
#     .Select('lambda j: j.pt()') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
#     .Select('lambda j: j.pt()') \
#     .Select('lambda pt1: pt1') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1].Select(lambda j1: (j1, j1))') \
#     .Select('lambda j: j[0].pt()') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1].SelectMany(lambda j1: (e1[0].runNumber(), e1[0].eventNumber(), j1.pt()))') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .Select('lambda e1: (e1[0].runNumber(), e1[0].eventNumber(), e1[1].Aggregate(0, lambda acc,v: acc + 1))') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'NJets']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .Select('lambda e1: (e1[0].runNumber(), e1[0].eventNumber(), e1[1].Select(lambda j: j.pt()).Max())') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'MaxJetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .Select('lambda e1: (e1[0].runNumber(), e1[0].eventNumber(), e1[1].Select(lambda j: j.pt()).Min())') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'MinJetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .Select('lambda e1: (e1[0].runNumber(), e1[0].eventNumber(), e1[1].Count())') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'MJets']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .Select('lambda e1: (e1[0].runNumber(), e1[0].eventNumber(), len(e1[1]))') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'MJets']).value()
# training_df = events \
#     .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
#     .Select('lambda j: j.pt()/1000.0') \
#     .Where('lambda j: 60.0 < 40.0') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
#     .Select('lambda j: j.pt()/1000.0') \
#     .Where('lambda pt: pt > 40.0') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")') \
#     .Select('lambda j: (j.pt()/1000.0,)') \
#     .Where('lambda pt: pt[0] > 40.0') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1].Select(lambda j1: (e1[0].runNumber(), e1[0].eventNumber(), j1.pt()/1000.0))') \
#     .Where('lambda info: info[2] > 40.0') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.Jets("AntiKt4EMTopoJets"), e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0))') \
#     .SelectMany('lambda evt: evt[0].Select(lambda j: (j, evt[1].Count()))') \
#     .Select('lambda e: e[1]') \
#     .AsPandasDF(columns=['nTracks']).value()
# -->
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"), e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0))') \
#     .SelectMany('lambda e1: e1[1].Select(lambda j1: (e1[0].runNumber(), e1[0].eventNumber(), j1.pt()/1000.0, e[2].Count()))') \
#     .Where('lambda info: info[2] > 40.0') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'JetPt', 'nTracks']).value()
# training_df = events.Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1]') \
#     .Select('lambda j: j.pt()') \
#     .AsPandasDF(columns=['JetPt']).value()
training_df = events.Select('lambda e: e.Jets("AntiKt4EMTopoJets")') \
    .SelectMany('lambda js: js') \
    .Select('lambda j: j.pt()/1000.0') \
    .AsPandasDF(columns=['JetPt']).value()

# Following works, but is commented out for now till we can integrate it above. Just
# for show, in short.
# track_pts = events.SelectMany(
#      'lambda e: e.Tracks("InDetTrackParticles")').Select("lambda t: (t.pt(), t.eta())")

# # Save it to a dataframe
# training_df = track_pts.AsPandasDF(columns=['TrackPt', 'TrackEta']).value()

print(training_df)
