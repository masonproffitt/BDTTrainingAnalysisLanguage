# Hold onto the generated code
from xAODlib.statement import block


class generated_code:
    def __init__(self):
        self._block = block()
        self._book_block = block()
        self._class_vars = []
        self._scope_stack = (self._block,)
        self._include_files = []

    def declare_class_variable(self, var):
        'Declare a variable as an instance of the query class. var must be a cpp_rep'
        self._class_vars += [var]

    def declare_variable(self, v):
        'Declare a variable at the current scope'
        self._scope_stack[-1].declare_variable(v)

    def add_statement(self, st):
        self._scope_stack[-1].add_statement(st)
        if isinstance(st, block):
            self._scope_stack = self._scope_stack + (st,)

    def add_include (self, path):
        self._include_files += [path]

    def include_files(self):
        return self._include_files

    def pop_scope(self):
        self._scope_stack[:-1]

    def current_scope(self):
        'Return a token that can be later used to set the scoping'
        return (self._scope_stack,)

    def set_scope(self, scope_info):
        self._scope_stack = scope_info[0]

    def add_book_statement(self, st):
        self._book_block.add_statement(st)

    def emit_query_code(self, e):
        'Emit query code'
        self._block.emit(e)

    def emit_book_code(self, e):
        'Emit the book method code'
        self._book_block.emit(e)

    def class_declaration_code(self):
        'Return the class variable decls'
        s = []
        for v in self._class_vars:
            s += ["{0} {1};\n".format(v.cpp_type(), v.as_cpp())]

        return s
