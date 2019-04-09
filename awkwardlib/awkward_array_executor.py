from pythonarraylib.python_array_executor import python_array_ast_visitor, python_array_executor

import awkward

import ast
import os

class ast_visitor(python_array_ast_visitor):
    pass

class awkward_array_executor(python_array_executor):
    def evaluate(self, ast_node):
        qv = ast_visitor()
        #print(ast.dump(ast_node))
        qv.visit(ast_node)
        if isinstance(self.dataset_source, str):
            data_pathname = self.dataset_source
        else:
            data_pathname = 'temp.awkd'
            awkward.save(data_pathname, self.dataset_source)
        f = open('temp.py', 'w')
        f.write('import awkward\n')
        source = ast_node.source
        while hasattr(source, 'source'):
            source = source.source
        f.write(source.rep + " = awkward.load('" + data_pathname + "')\n")
        f.write('output_array = ' + ast_node.rep + '\n')
        f.write("awkward.save('output.awkd', output_array)\n")
        f.close()
        os.system('python temp.py')
        if not isinstance(self.dataset_source, str):
            os.remove(data_pathname)
        os.remove('temp.py')
        output = awkward.load('output.awkd')
        os.remove('output.awkd')
        return output
