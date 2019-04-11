# Some tests to look at function simplifier

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

# Now the real test code starts.
from clientlib.function_simplifier import simplify_chained_calls, convolute
from clientlib.find_LINQ_operators import replace_LINQ_operators
from clientlib.ast_util import lambda_unwrap
from clientlib.call_stack import argument_stack
import ast
import copy

class normalize_ast(ast.NodeTransformer):
    '''
    The AST's can have the same symantec meaning, but not the same text, so the string compare that happens as part of these tests fail. The code
    here's job is to make the ast produced by the local code look like the python code.
    '''
    def __init__ (self):
        self._arg_index = 0
        self._arg_stack = argument_stack()

    def new_arg(self):
        'Generate a new argument, in a nice order'
        old_arg = self._arg_index
        self._arg_index += 1
        return "t_arg_{0}".format(old_arg)

    def start_visit(self, node):
        return self.visit(copy.deepcopy(node))

    def visit_Lambda(self, node):
        'Arguments need a uniform naming'
        a_mapping = [(a.arg, self.new_arg()) for a in node.args.args]

        # Remap everything that is inside this guy
        self._arg_stack.push_stack_frame()
        for m in a_mapping:
            self._arg_stack.define_name(m[0],m[1])
        body = self.visit(node.body)
        self._arg_stack.pop_stack_frame()

        # Rebuild the lambda guy
        args = [ast.arg(arg=m[1]) for m in a_mapping]
        return ast.Lambda(args=args, body=body)

    def visit_Name(self, node):
        return self._arg_stack.lookup_name(node.id)

def util_process(ast_in, ast_out):
    'Make sure ast in is the same as out after running through - this is a utility routine for the harness'

    # Make sure the arguments are ok
    a_source = ast_in if isinstance(ast_in, ast.AST) else ast.parse(ast_in)
    a_expected = ast_out if isinstance(ast_out, ast.AST) else ast.parse(ast_out)

    a_source_linq = replace_LINQ_operators().visit(a_source)
    a_expected_linq = replace_LINQ_operators().visit(a_expected)

    a_updated = simplify_chained_calls().visit(a_source_linq)

    s_updated = ast.dump(normalize_ast().visit(a_updated))
    s_expected = ast.dump(normalize_ast().visit(a_expected_linq))

    assert s_updated == s_expected

################
# Whitebox testing - make sure the convolute function code works. This
# is an internal method, so if it eventually disappears...

def util_test_conv(f1, f2, f_expected):
    a_1 = lambda_unwrap(ast.parse(f1))
    a_2 = lambda_unwrap(ast.parse(f2))
    a_expected = lambda_unwrap(ast.parse(f_expected))

    s_1 = ast.dump(normalize_ast().start_visit(a_1))
    s_2 = ast.dump(normalize_ast().start_visit(a_2))
    s_expected = ast.dump(normalize_ast().start_visit(a_expected))

    # Do the convolution
    a_conv = convolute(a_1, a_2)
    a_conv_reduced = simplify_chained_calls().visit(a_conv)

    s_conv_reduced = ast.dump(normalize_ast().start_visit(a_conv_reduced))
    s_1_after = ast.dump(normalize_ast().start_visit(a_1))
    s_2_after = ast.dump(normalize_ast().start_visit(a_2))

    # Make sure things match up with expected and nothing has changed.
    assert s_1 == s_1_after
    assert s_2 == s_2_after
    assert s_conv_reduced == s_expected

def test_convolute_simple_function():
    util_test_conv('lambda x: 1', 'lambda y: 2', 'lambda x: 1')

def test_convolute_addition():
    util_test_conv('lambda x: x+1', 'lambda y: y+h', 'lambda x:x + h + 1')

def test_convolute_compare():
    util_test_conv('lambda x: x>40', 'lambda j: j.pt', 'lambda j:j.pt>40')

################
# Test convolutions
def test_function_replacement():
    util_process('(lambda x: x+1)(z)', 'z+1')

def test_function_convolution_2deep():
    util_process('(lambda x: x+1)((lambda y: y)(z))', 'z+1')

def test_function_convolution_3deep():
    util_process('(lambda x: x+1)((lambda y: y)((lambda z: z)(a)))', 'a+1')

################
# Testing out Select from the start
#
def test_select_simple():
    # Select statement shouldn't be altered on its own.
    util_process("jets.Select(lambda j: j*2)", "jets.Select(lambda j: j*2)")

def test_select_select_convolution():
    util_process('jets.Select(lambda j: j).Select(lambda j2: j2*2)', 'jets.Select(lambda j2: j2*2)')

def test_select_identity():
    util_process('jets.Select(lambda j: j)', 'jets')

def test_where_simple():
    util_process('jets.Where(lambda j: j.pt>10)', 'jets.Where(lambda j: j.pt>10)')

################
# Test out Where
def test_where_always_true():
    util_process('jets.Where(lambda j: True)', 'jets')

def test_where_where():
    util_process('jets.Where(lambda j: j.pt>10).Where(lambda j1: j1.eta < 4.0)', 'jets.Where(lambda j: (j.pt>10) and (j.eta < 4.0))')

def test_where_select():
    util_process('jets.Select(lambda j: j.pt).Where(lambda p: p > 40)', 'jets.Where(lambda j: j.pt > 40).Select(lambda k: k.pt)')
#test_where_select()

def test_where_first():
    util_process('events.Select(lambda e: e.jets.First()).Select(lambda j: j.pt()).Where(lambda jp: jp>40.0)', \
        'events.Where(lambda e: e.jets.First().pt() > 40.0).Select(lambda e1: e1.jets.First().pt())')

################
# Testing out SelectMany
def test_selectmany_simple():
    # SelectMany statement shouldn't be altered on its own.
    util_process("jets.SelectMany(lambda j: j.tracks)", "jets.SelectMany(lambda j: j.tracks)")

###############
# Testing first

################
# Tuple tests
def test_tuple_select():
    # (t1, t2)[0] should be t1.
    util_process('(t1,t2)[0]', 't1')

def test_tuple_in_lambda():
    util_process('(lambda t: t[0])((j1, j2))', 'j1')

def test_tuple_in_lambda_2deep():
    util_process('(lambda t: t[0])((lambda s: s[1])((j0, (j1, j2))))', 'j1')

def test_tuple_around_first():
    util_process('events.Select(lambda e: e.jets.Select(lambda j: (j, e)).First()[0])', 'events.Select(lambda e: e.jets.First())')

def test_tuple_around_first_with_where():
    util_process('events.Select(lambda e: e.jets.Select(lambda j: (j, e)).First()[0]).Where(lambda j: j.pt>1000)',
        'events.Where(lambda e: e.jets.First().pt>1000).Select(lambda f: f.jets.First())')

# def test_tuple_many_layers():
#     util_process('events.Select(lambda e: (e, e.jets(), e.tracks()).Select(lambda i: i[1].Select(lambda j: (j,i[0],i[2])).First()).Where(lambda inf: inf[1].pt>1000))',
#             'events.Where(lambda e: e.jets().First().pt>1000).Select(lambda f: f.jets().Select(lambda j: (j, f, f.tracks()).First()))')