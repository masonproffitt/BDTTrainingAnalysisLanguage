# We will look for various things in the AST that, in the end, translate to the Aggregate terminal. And then translate them.
import ast

def generate_count_call (seq):
    r'''
        Given a sequence, generate an Aggregate call that will count the number
        of items in the sequence.

        seq: The sequence to be counted

        returns:
        agg_ast - An ast call to the Aggregate call.
    '''
    agg_lambda = ast.parse("lambda acc,v: acc + 1").body[0].value
    agg_start = ast.Num(0)

    new_call = ast.Call(func=ast.Attribute(attr="Aggregate", value=seq),args=[agg_start, agg_lambda])
    return new_call

class aggregate_node_transformer(ast.NodeTransformer):
    r'''
    Look for a few terminals and translate them into calls to Aggregate instead:

        Count()
    
    '''

    def visit_Count(self, node):
        return generate_count_call(node.source)

    def visit_Sum(self, node):
        # The lambda keep a running total.
        ast_lambda_acc = ast.parse("lambda acc,v: acc + v").body[0].value

        # Use a different flavor of aggregate
        new_call = ast.Call(ast.Attribute(attr="Aggregate", value=node.source),args=[ast_lambda_acc])
        return new_call

    def visit_Max(self, node):
        # The lambda will return the accumulator if is larger, otherwise the other guy. Parse b.c. we are lazy.
        ast_lambda_acc = ast.parse("lambda acc,v: acc if acc > v else v").body[0].value

        # Use a different flavor of aggregate
        new_call = ast.Call(ast.Attribute(attr="Aggregate", value=node.source),args=[ast_lambda_acc])
        return new_call

    def visit_Min(self, node):
        # The lambda will return the accumulator if is larger, otherwise the other guy. Parse b.c. we are lazy.
        ast_lambda_acc = ast.parse("lambda acc,v: acc if acc < v else v").body[0].value

        # Use a different flavor of aggregate
        new_call = ast.Call(ast.Attribute(attr="Aggregate", value=node.source),args=[ast_lambda_acc])
        return new_call

    def visit_Call(self, node):
        if type(node.func) is ast.Name:
            if (node.func.id == 'len') and (len(node.args) == 1):
                # This is a len(sequence) call, which should be turned into a .Count() call.
                return generate_count_call(node.args[0])
        return node
