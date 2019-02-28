# Collected code to get collections from the event object
import cpplib.cpp_ast as cpp_ast
import ast
from cpplib.cpp_vars import unique_name
from cpplib.cpp_representation import cpp_collection


def getCollectionJet(call_node):
    r'''
    Return a cpp ast for accessing the jet collection
    '''
    # Get the name jet collection to look at.
    if len(call_node.args) != 1:
        raise BaseException("Calling Jets - only one argument is allowed")
    if type(call_node.args[0]) is not ast.Str:
        raise BaseException("Calling Jets - only acceptable argument is a string")
    jet_collection_name = call_node.args[0].s

    # Fill in the CPP block next.
    r = cpp_ast.CPPCodeValue()
    r.replacements['collection_name'] = jet_collection_name
    r.include_files += ['xAODJet/JetContainer.h']

    r.running_code += ['const xAOD::JetContainer* result = 0;',
                        'ANA_CHECK (evtStore()->retrieve(result, collection_name));']
    r.result = 'result'
    r.result_rep = cpp_collection(unique_name("jets"), cpp_type="const xAOD::JetContainer*", is_pointer=True)

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node

# Config everything.
cpp_ast.method_names['Jets'] = getCollectionJet
