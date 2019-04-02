import ROOT

#RDF example
from clientlib.DataSets import EventDataSet

f = EventDataSet("data16_iso_728.root")
events = f.AsRDFEvents()
output = events.Select('lambda e: e.eventNumber').value()
print(output)

