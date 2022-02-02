

def get_base_url(base_url=None, backend=None):
    # Get the correct base url based on the values give for base_url and/or backend

    if base_url is not None:
        base_url = base_url
    elif backend is not None:
        base_url = "https://dispatcher-api.psi.ch/"+backend
    else:
        base_url = "https://dispatcher-api.psi.ch/sf-databuffer"

    return base_url
