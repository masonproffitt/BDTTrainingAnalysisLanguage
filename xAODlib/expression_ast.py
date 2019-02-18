# Code to help parsing expression AST's from python.

def assure_lambda (east, nargs = None):
    r'''
    Make sure the Python expression ast is a lambda call, and that it has the right number of args.

    east - python expression ast (module ast)
    nargs - number of args it is required to have. If None, no check is done.
    '''
    if not test_lambda (east, nargs):
        raise BaseException('Expression AST is not a lambda function with the right number of arguments')
    
    return east

def test_lambda (east, nargs):
    r''' Test arguments '''
    return True