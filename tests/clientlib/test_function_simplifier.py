# Some tests to look at function simplifier

# Following two lines necessary b.c. I can't figure out how to get pytest to pick up the python path correctly
# despite reading a bunch of docs.
import sys
sys.path.append('.')

from tests.clientlib.util_test_ast import *
from clientlib.find_LINQ_operators import replace_LINQ_operators
from clientlib.function_simplifier import simplify_chained_calls, convolute
from clientlib.ast_util import lambda_unwrap

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

def test_function_replacement_same_var_name():
    util_process('(lambda x: x+1)(x)', 'x+1')

def test_function_convolution_2deep():
    util_process('(lambda x: x+1)((lambda y: y)(z))', 'z+1')

def test_function_convolution_2deep_same_var_name():
    util_process('(lambda x: x+1)((lambda x: x)(x))', 'x+1')

def test_function_convolution_3deep():
    util_process('(lambda x: x+1)((lambda y: y)((lambda z: z)(a)))', 'a+1')

def test_function_convolution_3deep_same_var_name():
    util_process('(lambda x: x+1)((lambda x: x)((lambda x: x)(x)))', 'x+1')

################
# Testing out Select from the start
#
def test_where_simple():
    util_process('jets.Where(lambda j: j.pt>10)', 'jets.Where(lambda j: j.pt>10)')

def test_select_simple():
    # Select statement shouldn't be altered on its own.
    util_process("jets.Select(lambda j: j*2)", "jets.Select(lambda k: k*2)")

def test_select_select_convolution():
    util_process('jets.Select(lambda j: j).Select(lambda j2: j2*2)', 'jets.Select(lambda j2: j2*2)')

def test_select_select_convolution_with_same_vars():
    util_process('jets.Select(lambda j: j).Select(lambda j: j*2)', 'jets.Select(lambda k: k*2)')

def test_select_identity():
    util_process('jets.Select(lambda j: j)', 'jets')

def test_select_selectmany():
    util_process('e.SelectMany(lambda e: e.jets).Select(lambda j: j.pt)', 'e.SelectMany(lambda e: e.jets.Select(lambda j: j.pt))')

################
# Test out Where
def test_where_always_true():
    util_process('jets.Where(lambda j: True)', 'jets')

def test_where_where():
    util_process('jets.Where(lambda j: j.pt>10).Where(lambda j1: j1.eta < 4.0)', 'jets.Where(lambda j: (j.pt>10) and (j.eta < 4.0))')

def test_where_where_same():
    util_process('jets.Where(lambda j: j.pt>10).Where(lambda j: j.eta < 4.0)', 'jets.Where(lambda k: (k.pt>10) and (k.eta < 4.0))')

def test_where_select_var_name():
    util_process('jets.Select(lambda j: j.pt).Where(lambda p: p > 40)', 'jets.Where(lambda j: j.pt > 40).Select(lambda k: k.pt)')

def test_where_select_same_var_name():
    util_process('jets.Select(lambda j: j.pt).Where(lambda j: j > 40)', 'jets.Where(lambda k: k.pt > 40).Select(lambda i: i.pt)')

def test_where_first():
    util_process('events.Select(lambda e: e.jets.First()).Select(lambda j: j.pt()).Where(lambda jp: jp>40.0)', \
        'events.Where(lambda e: e.jets.First().pt() > 40.0).Select(lambda e1: e1.jets.First().pt())')

def test_where_first_same_var_name():
    util_process('events.Select(lambda e: e.jets.First()).Select(lambda j: j.pt()).Where(lambda j: j>40.0)', \
        'events.Where(lambda e: e.jets.First().pt() > 40.0).Select(lambda e1: e1.jets.First().pt())')

def test_where_select_with_same_var_name():
    util_process('jets.Select(lambda j: j.pt).Where(lambda j: j > 40)', 'jets.Where(lambda j: j.pt > 40).Select(lambda k: k.pt)')

def test_Where_with_variable_capture_simpler():
    util_process('events.SelectMany(lambda e: e.jets.Select(lambda j: (e, j))).Where(lambda et: et[0].runNumber>0).Select(lambda ett: ett[1].pt)',
            'events.SelectMany(lambda e: e.jets.Where(lambda j: e.runNumber > 0).Select(lambda j: j.pt))')
# It would be very nice if the above could figure out a lambda doesn't close over something, and then pop it up, but that
# is a whole other level of detecting.
#            'events.Where(lambda e: e.runNumber()>0).SelectMany(lambda e2: e2.jets.Select(lambda j3: j3.pt))')

def test_Where_with_variable_capture_same_var_name():
    util_process('events.SelectMany(lambda e: e.jets.Select(lambda j: (e, j))).Where(lambda e: e[0].runNumber>0).Select(lambda j: j[1].pt)',
            'events.SelectMany(lambda e: e.jets.Where(lambda j: e.runNumber > 0).Select(lambda j: j.pt))')

################
# Testing out SelectMany
def test_selectmany_simple():
    # SelectMany statement shouldn't be altered on its own.
    util_process("jets.SelectMany(lambda j: j.tracks)", "jets.SelectMany(lambda j: j.tracks)")

def test_selectmany_with_select():
    # This is where we want to end up
    util_process('e.SelectMany(lambda e: e.jets.Select(lambda j: j.pt))', 'e.SelectMany(lambda e: e.jets.Select(lambda j: j.pt))')

###############
# Testing first
def test_first_simple():
    util_process('jets.First().pt', 'jets.First().pt')

def test_first_simplified():
    util_process('jets.Select(lambda j: j).First()', 'jets.First()')

def test_first_tuple_simplified():
    util_process('jets.Select(lambda j: (j,j)).First()[0]', 'jets.First()')

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

def test_tuple_selectmany_first_noop():
    util_process('events.Select(lambda e: (e.jets, e.tracks.Where(lambda t: t.pt > 1000.0))).Select(lambda e1: e1[0].Select(lambda j: (j, e1[1])).First()).Select(lambda jInfo: jInfo[0])',
        'events.Select(lambda e: e.jets.First())')

def test_tuple_selectmany_var_capture():
    util_process('e.SelectMany(lambda e: e.jets.Select(lambda j: (e, j))).Select(lambda j: j[1].pt)', 'e.SelectMany(lambda e: e.jets.Select(lambda j: j.pt))')

def test_tuple_selectmany_var_capture_2():
    util_process('e.SelectMany(lambda e: e.jets.Select(lambda j: (e, j)).Select(lambda j: j[1].pt))', 'e.SelectMany(lambda e: e.jets.Select(lambda j: j.pt))')

# More complex ones that are actually several things.
def test_complex_1():
    util_process('events.Select(lambda e: (e.Jets, e.Tracks.Where(lambda t: t.pt > 1000.0))).Select(lambda e1: e1[0].Select(lambda j: (j,e1[1])).First()).Select(lambda jInfo: jInfo[1].Count())',
        'events.Select(lambda e: e.Jets.Select(lambda j: e.Tracks.Where(lambda t: t.pt > 1000.0)).First().Count())')
