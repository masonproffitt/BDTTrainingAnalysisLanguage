# Hold onto the generated code

class generated_code:
    def __init__ (self):
        self._statements = []

    def add_statement(self, st):
        self._statements += [st]

