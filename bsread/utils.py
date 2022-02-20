import re


def get_base_url(base_url=None, backend=None):
    # Get the correct base url based on the values give for base_url and/or backend

    if base_url is not None:
        base_url = base_url
    elif backend is not None:
        base_url = "https://dispatcher-api.psi.ch/"+backend
    else:
        base_url = "https://dispatcher-api.psi.ch/sf-databuffer"

    return base_url


def check_and_update_uri(uri, default_port=9999, exception=ValueError):

    if not re.match('^tcp://', uri):
        # print('Protocol not defined for address - Using tcp://')
        uri = 'tcp://' + uri
    if not re.match('.*:[0-9]+$', uri):
        # print('Port not defined for address - Using 9999')
        uri += f':{default_port}'
    if not re.match(r"^tcp://[a-zA-Z.\-0-9]+:[0-9]+$", uri):
        raise exception(f"{uri} - Invalid URI")

    return uri
