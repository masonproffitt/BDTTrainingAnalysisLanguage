# We will look for various things in the AST that, in the end, translate to the Aggregate terminal. And then translate them.
import ast

class aggregate_node_transformer(ast.NodeTransformer):
    r'''
    Look for a few terminals and translate them into calls to Aggregate instead:

        Count()
    
    '''

    def visit_Call(self, node):
        if type(node.func) is ast.Attribute:
            if node.func.attr == "Count":
                # The lambda that will return acculator + 1 (being lazy here, probably faster to construct than parse, but...)
                agg_lambda = ast.parse("lambda acc,v: acc + 1").body[0].value
                agg_start = ast.Num(0)

                new_call = ast.Call(ast.Attribute(attr="Aggregate", value=node.func.value),args=[agg_start, agg_lambda])
                return new_call
        return node