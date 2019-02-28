# Hold onto the generated code
from xAODlib.statement import block


class generated_code:
    def __init__(self):
        self._block = block()
        self._book_block = block()
        self._class_vars = []
        self._scope_stack = [self._block]
        self._include_files = []

    def declare_class_variable(self, type, name):
        'Declare a variable as an instance of the query class'
        self._class_vars += [(type, name)]

    def declare_variable(self, type, name):
        'Declare a variable at the current scope'
        self._scope_stack[-1].declare_variable(type, name)

    def add_statement(self, st):
        self._scope_stack[-1].add_statement(st)
        if isinstance(st, block):
            self._scope_stack.append(st)

    def add_include (self, path):
        self._include_files += [path]

    def include_files(self):
        return self._include_files

    def pop_scope(self):
        self._scope_stack.pop()

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
        for name, v in self._class_vars:
            s += ["{0} {1};\n".format(name, v)]

        return s
