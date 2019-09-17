from pythonarraylib.python_array_ast_visitor import python_array_ast_visitor

import ast

def get_roundtrip_string(string):
  visitor = python_array_ast_visitor()
  return visitor.get_rep(ast.parse(string))

def check_roundtrip_string(string):
  assert get_roundtrip_string(string) == string

def test_empty():
  check_roundtrip_string('')

def test_Num():
  check_roundtrip_string('3.14')

def test_Str():
  check_roundtrip_string("'qwerty'")

def test_empty_List():
  check_roundtrip_string('[]')

def test_nonempty_List():
  check_roundtrip_string('[1, 2, 3]')

def test_empty_Tuple():
  check_roundtrip_string('()')

def test_nonempty_Tuple():
  check_roundtrip_string('(1, 2, 3)')

def test_empty_Dict():
  check_roundtrip_string('{}')

def test_nonempty_Dict():
  check_roundtrip_string("{'a': 1, 'b': 2, 'c': 3}")

def test_empty_NameConstant():
  check_roundtrip_string('None')

def test_UnaryOp():
  check_roundtrip_string('(-1)')

def test_BinOp():
  check_roundtrip_string('(1 + 2)')

def test_BoolOp():
  check_roundtrip_string('(1 and 0)')

def test_binary_Compare():
  check_roundtrip_string('(1 > 2)')

def test_ternary_Compare():
  check_roundtrip_string('(1 > 2 > 3)')

# TODO: deal with axis parameter so that this can be tested here
#def test_Subscript():
#  check_roundtrip_string('[1, 2, 3][0]')
