import requests
import json

base_url = 'http://localhost:8080'


# Configure a source
def configure_source(address):
    """
    Configure a data source - as input to the dispatching layer
    Args:
        address:    Address of the source, e.g. tcp://localhost:9999

    Returns:

    """
    config = {"sources": [{"stream": address}]}
    headers = {'content-type': 'application/json'}
    response = requests.post(base_url+'/sources', data=json.dumps(config), headers=headers)
    if not response.ok:
        raise Exception('Unable to configure source - '+response.text)


# Get currently configured sources
def get_sources():
    """

    Returns: Configured sources - e.g. [{"stream":"tcp://localhost:9999"}]

    """
    response = requests.get(base_url+'/sources')

    if not response.ok:
        raise Exception('Unable to retrieve configured sources - ' + response.text)

    return response.json()


# In[30]:

# Delete source
config = {"sources": [{"stream": "tcp://localhost:9999"}]}
headers = {'content-type': 'application/json'}
response = requests.delete(base_url+'/sources', data=json.dumps(config), headers=headers)
print(response)
print(response.text)


# In[99]:

# Request stream
config = {"channels":[{"name":"Int16Waveform"},{"name":"UInt16Waveform"}], "streamType":"push_pull"}
headers = {'content-type': 'application/json'}
response = requests.post(base_url+'/stream', data=json.dumps(config), headers=headers)
print(response)
print(response.text)


# In[98]:

# Get streams currently requested
response = requests.get(base_url+'/streams')
print(response)
print(response.text)


# In[57]:

# Delete stream

config = "tcp://pineapple.psi.ch:50805"
headers = {'content-type': 'application/json'}
response = requests.delete(base_url+'/stream', data=json.dumps(config), headers=headers)

# config = "tcp://pineapple.psi.ch:50727"
# headers = {'content-type': 'text/plain'}
# response = requests.delete(base_url+'/stream', data=config, headers=headers)
print(response)
print(response.text)