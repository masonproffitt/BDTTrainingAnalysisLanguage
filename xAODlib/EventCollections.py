# Collected code to get collections from the event object
import cpplib.cpp_ast as cpp_ast
import ast
from cpplib.cpp_vars import unique_name
import cpplib.cpp_representation as crep
import cpplib.cpp_types as ctyp
import copy

# Need a type for our type system to reason about the containers.
class event_collection_container:
    def __init__(self, type_name, is_pointer = True):
        self._type_name = type_name
        self._is_pointer = is_pointer

    def is_pointer(self):
        'All ATLAS event collections are pointers'
        return True

    def __str__(self):
        return "const {0}*".format(self._type_name)

class event_collection_collection(event_collection_container):
    def __init__(self, type_name, element_name):
        event_collection_container.__init__(self, type_name)
        self._element_name = element_name

    def element_type(self):
        'Return the type of the elements in the collection'
        return ctyp.terminal(self._element_name, is_pointer=True)

    def dereference(self):
        'Return a new version of us that is not a pointer'
        new_us = copy.copy(self)
        new_us.is_pointer = False
        return new_us

# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
collections = [
    {
        'function_name': "Jets",
        'include_files': ['xAODJet/JetContainer.h'],
        'container_type':  event_collection_collection('xAOD::JetContainer', 'xAOD::Jet'),
    },
    {
        'function_name': "Tracks",
        'include_files': ['xAODTracking/TrackParticleContainer.h'],
        'container_type': event_collection_collection('xAOD::TrackParticleContainer', 'xAOD::TrackParticle')
    },
    {
        'function_name': "EventInfo",
        'include_files': ['xAODEventInfo/EventInfo.h'],
        'container_type': event_collection_container('xAOD::EventInfo'),
        'is_collection': False,
    },
    {
        'function_name': "TruthParticles",
        'include_files': ['xAODTruth/TruthParticleContainer.h', 'xAODTruth/TruthParticle.h', 'xAODTruth/TruthVertex.h'],
        'container_type': event_collection_collection('xAOD::TruthParticleContainer', 'xAOD::TruthParticle')
    },
]

def getCollection(info, call_node):
    r'''
    Return a cpp ast for accessing the jet collection
    '''
    # Get the name jet collection to look at.
    if len(call_node.args) != 1:
        raise BaseException("Calling {0} - only one argument is allowed".format(info['function_name']))
    if type(call_node.args[0]) is not ast.Str:
        raise BaseException("Calling {0} - only acceptable argument is a string".format(info['function_name']))

    # Fill in the CPP block next.
    r = cpp_ast.CPPCodeValue()
    r.args = ['collection_name',]
    r.include_files += info['include_files']

    r.running_code += ['{0} result = 0;'.format(info['container_type']),
                        'ANA_CHECK (evtStore()->retrieve(result, collection_name));']
    r.result = 'result'

    is_collection = info['is_collection'] if 'is_collection' in info else True
    if is_collection:
        r.result_rep = lambda scope: crep.cpp_collection(unique_name(info['function_name'].lower()), scope=scope, collection_type=info['container_type'])
    else:
        r.result_rep = lambda scope: crep.cpp_variable(unique_name(info['function_name'].lower()), scope=scope, cpp_type=info['container_type'])

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node

# Config everything.
def create_higher_order_function(info):
    'Creates a higher-order function because python scoping is broken'
    return lambda call_node: getCollection(info, call_node)

for info in collections:
    cpp_ast.method_names[info['function_name']] = create_higher_order_function(info)
