from clientlib.DataSets import ArrayDataSet

import awkward

awkward_arrays = {'eventNumber': awkward.fromiter([0, 1, 2]),
                  'jet_pT': awkward.fromiter([[12.3], [], [45.6, 78.9]])}
awkward_dataset = ArrayDataSet(awkward_arrays)
awkward_array_stream = awkward_dataset.AsAwkwardArray()

def test_Select_one_column():
  query = awkward_array_stream.Select('lambda e: e.eventNumber')
  assert query.value().tolist() == awkward_arrays['eventNumber'].tolist()

# For now tuples and lists are just turned into Tables
# TODO: fix this with list comprehensions
#
#def test_Select_tuple():
#  query = awkward_array_stream.Select("lambda e: (e.eventNumber, e.jet_pT)")
#  value = query.value()
#  assert type(value) is tuple
#  assert len(value) == 2
#  assert value[0].tolist()  == awkward_arrays['eventNumber'].tolist()
#  assert value[1].tolist()  == awkward_arrays['jet_pT'].tolist()
#
#def test_Select_list():
#  query = awkward_array_stream.Select("lambda e: [e.eventNumber, e.jet_pT]")
#  value = query.value()
#  assert type(value) is list
#  assert len(value) == 2
#  assert value[0].tolist()  == awkward_arrays['eventNumber'].tolist()
#  assert value[1].tolist()  == awkward_arrays['jet_pT'].tolist()

def test_Select_dict():
  query = awkward_array_stream.Select("lambda e: {'eventNumber': e.eventNumber, 'jet_pT': e.jet_pT}")
  value = query.value()
  assert set(value.columns) == set(['eventNumber', 'jet_pT'])
  assert value['eventNumber'].tolist()  == awkward_arrays['eventNumber'].tolist() == [0, 1, 2]
  assert value['jet_pT'].tolist()  == awkward_arrays['jet_pT'].tolist() == [[12.3], [], [45.6, 78.9]]

def test_SelectMany_one_column():
  query = awkward_array_stream.SelectMany('lambda e: e.jet_pT')
  assert query.value().tolist() == awkward_arrays['jet_pT'].flatten().tolist() == [12.3, 45.6, 78.9]

def test_Where_one_column_event_level():
  query = awkward_array_stream.Select('lambda e: e.eventNumber').Where('lambda eventNumber: eventNumber > 0')
  assert query.value().tolist() == awkward_arrays['eventNumber'][1:].tolist() == [1, 2]

def test_Where_one_column_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Where(lambda jet_pT: jet_pT < 50)')
  assert query.value().tolist() == awkward_arrays['jet_pT'][awkward_arrays['jet_pT'] < 50].tolist() == [[12.3], [], [45.6]]

def test_Count_event_level():
  # passing the data source through doesn't work yet
  # TODO: fix this by inspecting the type of base_array
  #query = awkward_array_stream.Select('lambda e: e').Count()
  query = awkward_array_stream.Select('lambda e: e.eventNumber').Count()
  assert query.value() == len(awkward_arrays['eventNumber']) == 3

def test_Count_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Count()')
  assert query.value().tolist() == awkward_arrays['jet_pT'].count().tolist() == [1, 0, 2]

# TODO: add to ObjectStream
#def test_Min_event_level():
#  query = awkward_array_stream.Select('lambda e: e.eventNumber').Min()
#  assert query.value() == awkward_arrays['eventNumber'].min() == 0
#def test_Max_event_level():
#  query = awkward_array_stream.Select('lambda e: e.eventNumber').Max()
#  assert query.value() == awkward_arrays['eventNumber'].max() == 2
#def test_Sum_event_level():
#  query = awkward_array_stream.Select('lambda e: e.eventNumber').Sum()
#  assert query.value() == awkward_arrays['eventNumber'].sum() == 3
#def test_Average_event_level():
#  query = awkward_array_stream.Select('lambda e: e.eventNumber').Average()
#  assert query.value() == awkward_arrays['eventNumber'].mean() == 1

def test_Min_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Min()')
  assert query.value().tolist() == awkward_arrays['jet_pT'].min().tolist() == [12.3, float('inf'), 45.6]

def test_Max_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Max()')
  assert query.value().tolist() == awkward_arrays['jet_pT'].max().tolist() == [12.3, float('-inf'), 78.9]

def test_Sum_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Sum()')
  assert query.value().tolist() == awkward_arrays['jet_pT'].sum().tolist() == [12.3, 0, 45.6 + 78.9]

def test_Average_jet_level():
  query = awkward_array_stream.Select('lambda e: e.jet_pT.Average()')
  value = query.value()
  comparison = awkward_arrays['jet_pT'].mean().tolist()
  assert value[0] == comparison[0] == 12.3
  assert value[1] != value[1] and comparison[1] != comparison[1]
  assert value[2] == comparison[2] == (45.6 + 78.9) / 2.0

def test_First_one_column_event_level():
  query = awkward_array_stream.Select('lambda e: e.eventNumber').First()
  assert query.value() == awkward_arrays['eventNumber'][0] == 0

modified_awkward_arrays = {'eventNumber': awkward.fromiter([0, 2]),
                           'jet_pT': awkward.fromiter([[12.3], [45.6, 78.9]])}
modified_awkward_dataset = ArrayDataSet(modified_awkward_arrays)
modified_awkward_array_stream = modified_awkward_dataset.AsAwkwardArray()

def test_First_one_column_jet_level():
  query = modified_awkward_array_stream.Select('lambda e: e.jet_pT.First()')
  assert query.value().tolist() == modified_awkward_arrays['jet_pT'][:, 0].tolist()

empty_array = awkward.fromiter([])
empty_dataset = ArrayDataSet(empty_array)
empty_array_stream = awkward_dataset.AsAwkwardArray()

def test_emtpy_dataset():
  query = empty_array_stream.Select('lambda e: None')
  assert query.value() is None
