

def init_routers(api, l):
    """
    Initializes application routing
    """
    for r in l:
        args, kwargs = r
        api.add_resource(*args, **kwargs)

    return api
