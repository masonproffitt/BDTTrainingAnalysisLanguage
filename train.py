# Run the training

# Get the import working from local files
from clientlib.DataSets import EventDataSet
from cpplib.math_utils import DeltaR

# Dump the C++ so we can see what is going on.
import xAODlib.atlas_xaod_executor
xAODlib.atlas_xaod_executor.dump_cpp = True

# The input file we are going to use to do the training
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")
#f = EventDataSet(r"file://C:/Users/gordo/Documents/mc16_13TeV/AOD.16300985._000011.pool.root.1")

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
# training_df = events.Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"))') \
#     .SelectMany('lambda e1: e1[1]') \
#     .Select('lambda j: j.pt()') \
#     .AsPandasDF(columns=['JetPt']).value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"), e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0))') \
#     .SelectMany('lambda e1: e1[1].Select(lambda j: (e1[0].runNumber(), e1[2].Count(), j.pt()/1000.0))') \
#     .Where('lambda e2: e2[2] > 40.0') \
#     .AsPandasDF(columns=['run', 'nTrack', 'jetPt']) \
#     .value()
# training_df = events \
#     .Select('lambda e: (e.EventInfo("EventInfo"), e.Jets("AntiKt4EMTopoJets"), e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0))') \
#     .SelectMany('lambda e1: e1[1].Select(lambda j1: (e1[0].runNumber(), e1[0].eventNumber(), j1.pt()/1000.0, e1[2].Count()))') \
#     .Where('lambda e2: e2[2] > 40.0') \
#     .AsPandasDF(columns=['RunNumber', 'EventNumber', 'JetPt', 'nTracks']).value()
# training_df = events \
#             .Select("lambda e: (e.EventInfo('EventInfo'), e.Jets('AntiKt4EMTopoJets'), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .SelectMany('lambda e1: e1[1].Select(lambda j: (e1[0],j,e1[2]))') \
#             .Select('lambda jInfo: (jInfo[0].runNumber(), jInfo[0].eventNumber(), jInfo[1].pt()/1000.0, jInfo[1].eta(), jInfo[2].Where(lambda t1: DeltaR(t1.eta(), t1.phi(), jInfo[1].eta(), jInfo[1].phi()) < 0.2).Count())') \
#             .Where('lambda jInfo1: jInfo1[2] > 40.0') \
#             .AsPandasDF(columns=['Run', 'Event', 'JetPt', 'JetEta', 'NTracks']) \
#             .value()
# training_df = events \
#             .Select("lambda e: (e.EventInfo('EventInfo'), e.Jets('AntiKt4EMTopoJets').Where(lambda j: j.pt()/1000.0 > 40.0), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .Select('lambda j1: (j1[0].runNumber(), j1[0].eventNumber(), j1[1].Select(lambda j2: j2.pt()/1000.0), j1[1].Select(lambda j3: j3.eta()), j1[2].Select(lambda t2: t2.pt()/1000.0))') \
#             .AsAwkwardArray(columns=['Run', 'Event', 'JetPts', 'JetEtas', 'TrackPts']) \
#             .value()
# training_df = events \
#             .Select("lambda e: e.Jets('AntiKt4EMTopoJets').First()") \
#             .Select("lambda j: (j.pt(), j.eta())") \
#             .AsPandasDF(columns=['JetPt', 'JetEta']) \
#             .value()
# training_df = events \
#             .Select("lambda e: (e.Jets('AntiKt4EMTopoJets'), e)[0].First()") \
#             .Select("lambda j: (j.pt(), j.eta())") \
#             .AsPandasDF(columns=['JetPt', 'JetEta']) \
#             .value()
# training_df = events \
#             .Select("lambda e: e.Jets('AntiKt4EMTopoJets').Select(lambda j1: (j1, e)).First()[0]") \
#             .Select("lambda j: (j.pt(), j.eta())") \
#             .AsPandasDF(columns=['JetPt', 'JetEta']) \
#             .value()
# training_df = events \
#         .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
#         .AsPandasDF('dude') \
#         .value()
# training_df = events \
#         .Select('lambda e: e.Jets("AntiKt4EMTopoJets").First().pt()/1000.0') \
#         .AsPandasDF('FirstJetPt') \
#         .value()
# training_df = events \
#         .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).First()') \
#         .AsPandasDF('FirstJetPt') \
#         .value()
# training_df = events \
#         .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: j.pt()/1000.0).Where(lambda jpt: jpt > 10.0).First()') \
#         .AsPandasDF('FirstJetPt') \
#         .value()

# -->
# training_df = events \
#             .Select("lambda e: (e.EventInfo('EventInfo'), e.Jets('AntiKt4EMTopoJets'), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .Select('lambda e1: e1[1].Select(lambda j: (e1[0],j,e1[2])).First()') \
#             .Select('lambda jInfo: (jInfo[0].runNumber(), jInfo[0].eventNumber(), jInfo[1].pt()/1000.0, jInfo[1].eta(), jInfo[2].Where(lambda t1: DeltaR(t1.eta(), t1.phi(), jInfo[1].eta(), jInfo[1].phi()) < 0.2).Count())') \
#             .Where('lambda jInfo1: jInfo1[2] > 40.0') \
#             .AsPandasDF(columns=['Run', 'Event', 'JetPt', 'JetEta', 'NTracks']) \
#             .value()
# This generates bad code
# training_df = events \
#             .Select("lambda e: (e.EventInfo('EventInfo'), e.Jets('AntiKt4EMTopoJets'), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .Select('lambda e1: e1[1].Select(lambda j: (e1[0],j,e1[2])).First()') \
#             .Select('lambda jInfo: (jInfo[0].runNumber(), jInfo[0].eventNumber(), jInfo[1].pt()/1000.0, jInfo[1].eta())') \
#             .AsPandasDF(columns=['Run', 'Event', 'JetPt', 'JetEta']) \
#             .value()
# Makes for bad code
# training_df = events \
#             .Select("lambda e: (e.Jets('AntiKt4EMTopoJets'), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .Select('lambda jInfo: (jInfo[1].Where(lambda t1: DeltaR(t1.eta(), t1.phi(), jInfo[0].eta(), jInfo[0].phi()) < 0.2).Count(),)') \
#             .AsPandasDF(columns=['NTracks']) \
#             .value()
# training_df = events \
#             .Select("lambda e: (e.Jets('AntiKt4EMTopoJets'), e.Tracks('InDetTrackParticles').Where(lambda t: t.pt() > 1000.0))") \
#             .Select('lambda e1: e1[0].Select(lambda j: (j,e1[1])).First()') \
#             .Select('lambda jInfo: (jInfo[1].Count(),)') \
#             .AsPandasDF(columns=['NTracks']) \
#             .value()

# training_df = events \
#                 .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles")).First().Count()') \
#                 .AsPandasDF('dude') \
#                 .value()
# training_df = events \
#                 .SelectMany('lambda e: e.Jets("AntiKt4EMTopoJets")').Select('lambda j: j.pt()').AsPandasDF('dude').value()

        # .Select('lambda e: e.Jets("AntiKt4EMTopoJets").Select(lambda j: e.Tracks("InDetTrackParticles").Where(lambda t: t.pt() > 1000.0)).First().Count()') \
        # .AsPandasDF('dude') \
        # .value()

# print(training_df)

import tests.xAODlib.test_atlas_xaod_executor as xaod_tests 
#xaod_tests.test_Select_is_an_array()
xaod_tests.test_per_event_item()
#import tests.xAODlib.test_integrated_query as integrated_tests
#integrated_tests.test_First_two_outer_loops()
#xaod_tests.test_Select_is_not_an_array()