# Run the training

# Get the import working from local files
from clientlib.DataSets import EventDataSet

# The input file we are going to use to do the training
f = EventDataSet(r"file://G:/mc16_13TeV/AOD.16300985._000011.pool.root.1")

# Turn into an event stream that is known by ATLAS.
events = f.AsATLASEvents()

# Next, get the jet pT's, which we want to look at.
jet_pts = events.SelectMany(lambda e: e.Jets).Calibrate().Select(lambda j: j.pT)

# Save it to a dataframe
training_df = jet_pts.AsPandasDF(columns=['JetPt']).value()

print (training_df)
