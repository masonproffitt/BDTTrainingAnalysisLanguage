# Statements


class block:
    'This is a bock of statements surrounded by a scoping (like open close bracket, for loop, etc.)'

    def __init__(self):
        self._statements = []

    def add_statement(self, s):
        'Add statement s to the list of statements'
        self._statements += [s]

    def emit(self, e):
        'Render the block of code'
        e.add_line("{")
        for s in self._statements:
            s.emit(e)
        e.add_line("}")


class loop(block):
    'A for loop'

    def __init__(self, collection_name, loop_variable):
        block.__init__(self)
        self._collection_name = collection_name
        self._loop_variable = loop_variable

    def emit(self, e):
        'Emit a for loop enclosed by a block of code'
        e.add_line("for (auto {0} : {1})".format(
            self._loop_variable, self._collection_name))
        block.emit(self, e)


class book_ttree:
    'Book a TTree for writing out. Meant to be in the Book method'

    def __init__(self, tree_name, leaves):
        self._tree_name = tree_name
        self._leaves = leaves

    def emit(self, e):
        'Emit the book statement for a tree'
        e.add_line('ANA_CHECK (book (TTree ("{0}", "My analysis ntuple")));'.format(
            self._tree_name))
        e.add_line('auto mytree = tree ("{0}");'.format(self._tree_name))
        for var_pair in self._leaves:
            e.add_line(
                'mytree->Branch("{0}", &{1});'.format(var_pair[0], var_pair[1]))


class ttree_fill:
    'Fill a TTree'

    def __init__(self, tree_name):
        self._tree_name = tree_name

    def emit(self, e):
        e.add_line('tree("{0}")->Fill();'.format(self._tree_name))


class xaod_get_collection:
    def __init__(self, collection_name, var_name):
        self._collection_name = collection_name
        self._var_name = var_name

    def emit(self, e):
        e.add_line("const xAOD::JetContainer* {0} = 0;".format(self._var_name))
        e.add_line('ANA_CHECK (evtStore()->retrieve( {0}, "{1}"));'.format(
            self._var_name, self._collection_name))


class set_var:
    'Set a variable to a value'

    def __init__(self, target_var, value_var):
        self._target = target_var
        self._value = value_var

    def emit(self, e):
        e.add_line('{0} = {1};'.format(self._target, self._value))
