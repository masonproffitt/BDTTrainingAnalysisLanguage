# Event stream from ATLAS
from clientlib.EventStream import EventStream
from atlaslib.atlas_xaod_executor import atlas_xaod_executor
from clientlib.query_ast import base_ast
from atlaslib.cpp_representation import cpp_rep_base, cpp_variable, cpp_collection
import ast
import atlaslib.expression_ast as expression_ast
import atlaslib.statement as statement

# TODO: Reorg the file so that it makes more sense from the readability POV
# TODO: "ast" should be either east or qast depending if it is a query or a expression ast.

class xAOD_event_expression_parser(ast.NodeVisitor):
    'Generate code to access an xAOD expression'

    def __init__(self, gc):
        'Keep track of the generated code object so we can use it as we need'
        self._gc = gc
        self._var_dict = {}
        self._result = None

    def visit_Lambda(self, lambda_node):
        'Record this variable name so when we see references to it we know it is the event store'
        self._var_dict[lambda_node.args.args[0].arg] = "EVENT"
        ast.NodeVisitor.visit(self, lambda_node.body)
        del self._var_dict[lambda_node.args.args[0].arg]

    def resolve_id (self, id):
        'Look up the  in our local dict'
        return self._var_dict[id] if id in self._var_dict else id

    def visit_Call(self, call_node):
        r'''
        We really only know how to fetch things out of the main collection. So this is a very limited call.
        '''
        
        # handel only if this is a call against event.
        object_call_against = self.resolve_id(call_node.func.value.id)
        object_call_method = call_node.func.attr

        # Get the arguments.
        collection_name = call_node.args[0].s

        # Make sure we are calling against EVENT.
        if object_call_against is not "EVENT":
            raise BaseException("Only calls against EVENT are supported")

        # Ok, code up access to the collection.
        if object_call_method == "Jets":
            self._gc.add_statement(statement.xaod_get_collection(collection_name, "jets"))
            self._result = cpp_collection("jets", is_pointer=True)
        else:
            raise BaseException ("Only Jets is understood right now")



class atlas_xAOD_collection_rep(cpp_rep_base):
    r'''
    The xAOD data bus collection. This allows for access to the various
    objects (like jets) that are stored inside it.
    '''

    def access_collection(self, gen_code, access_ast):
        r'''
        Code up access to a particular collection. The ast needs to give us enough information
        to know what the hell we are after (type, etc.)
        '''
        expression_ast.assure_labmda(access_ast, nargs=1)

        v = xAOD_event_expression_parser(gen_code)
        v.visit(access_ast._selection_function)
        return v._result


class atlas_file_event_stream_ast (base_ast):
    r"""
    An AST node that represents the event source.
    """
    def __init__ (self, ds_url):
        base_ast.__init__(self, None)
        self._ds = ds_url
        self._rep = None

    def get_executor(self):
        return atlas_xaod_executor(self._ds)

    def visit_ast(self, visitor):
        visitor.visit_atlas_file_event_stream_ast(self)

    def get_rep(self):
        '''Return the representation for this file'''
        if self._rep is None:
            self._rep = atlas_xAOD_collection_rep()
        return self._rep

class AtlasEventStream(EventStream):
    r"""
    A stream of events from an ATLAS xAOD file.
    """
    def __init__(self, evt_stream):
        EventStream.__init__(self, atlas_file_event_stream_ast(evt_stream._url))
