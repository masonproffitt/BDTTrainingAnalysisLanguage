# Run the training

# Get the import working from local files
from clientlib.DataSets import EventDataSet
import xAODlib.Jets

# The input file we are going to use to do the training
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")

# Turn into an event stream that is known by ATLAS.
events = f.AsATLASEvents()

# Next, get the jet pT's, which we want to look at.
jet_pts = events.SelectMany(
    'lambda e: e.Jets("AntiKt4EMTopoJets")').Select("lambda j: (j.pt(), j.eta(), j.getMomentFloat('Width'))")

# Save it to a dataframe
training_df = jet_pts.AsPandasDF(columns=['JetPt', 'JetEta', 'JetWidth']).value()

print(training_df)
