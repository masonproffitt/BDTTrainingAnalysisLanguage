from pythonarraylib.python_array_executor import python_array_executor

from awkwardarraylib.awkward_array_node_transformer import awkward_array_node_transformer
from awkwardarraylib.awkward_array_ast_visitor import awkward_array_ast_visitor

import awkward

import ast
import os

class awkward_array_executor(python_array_executor):
    def apply_ast_transformations(self, tree):
        print(ast.dump(tree))
        return awkward_array_node_transformer().visit(tree)

    def evaluate(self, ast_node):
        print(ast.dump(ast_node))
        qv = awkward_array_ast_visitor()
        qv.visit(ast_node)
        print(ast.dump(ast_node))
        if isinstance(self.dataset_source, str):
            data_pathname = self.dataset_source
        else:
            data_pathname = 'temp.awkd'
            awkward.save(data_pathname, self.dataset_source, mode='w')
        f = open('temp.py', 'w')
        f.write('import awkward\n')
        source = ast_node.source
        while hasattr(source, 'source'):
            source = source.source
        if data_pathname[-5:] == '.awkd':
            f.write(source.rep + " = awkward.load('" + data_pathname + "')\n")
        elif data_pathname[-5:] == '.root':
            f.write('import uproot\n')
            f.write("input_file = uproot.open('" + data_pathname + "')\n")
            f.write(source.rep + " = input_file[input_file.keys()[0]].lazyarrays(namedecode='utf-8')\n")
        else:
            raise BaseException('unimplemented file type: ' + data_pathname)
        f.write('output_array = ' + ast_node.rep + '\n')
        f.write("awkward.save('output.awkd', output_array, mode='w')\n")
        f.close()
        os.system('python temp.py')
        if not isinstance(self.dataset_source, str):
            os.remove(data_pathname)
        #os.remove('temp.py')
        output = awkward.load('output.awkd')
        os.remove('output.awkd')
        return output
