from awkwardarraylib.awkward_array_ast_visitor import awkward_array_ast_visitor

import ast

def get_roundtrip_string(string):
  visitor = awkward_array_ast_visitor()
  return visitor.get_rep(ast.parse(string))

def check_roundtrip_string(string):
  assert get_roundtrip_string(string) == string

def test_global_Name():
  check_roundtrip_string('awkward')

def test_Lambda():
  check_roundtrip_string('(lambda x: x)')

def test_Call():
  initial_string = '[1, 1, 3].count(1)'
  assert eval(get_roundtrip_string(initial_string)) == eval(initial_string) == 2
