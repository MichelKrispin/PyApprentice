public_variable = 10

private_variable = 2

def public_function():
    return "public information"

def private_function():
    return "super sensitive information"

safe_list = ['public_variable', 'public_function']
safe_dict = dict([ (k, locals().get(k, None)) for k in safe_list ])
# add any needed builtins back in
safe_dict['len'] = len

eval("public_variable+2", {"__builtins__" : None }, safe_dict)
