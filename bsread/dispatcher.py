import requests
import json

import logging

base_url = 'http://localhost:8080'
base_url = 'http://dispatcher-api.psi.ch/sf'


def add_input_sources(addresses):
    """
    Add a input source to the dispatching layer
    Args:
        addresses:    Address of the source, e.g. tcp://localhost:9999

    Returns:

    """
    config = {"sources": []}

    if isinstance(addresses, list):
        for address in addresses:
            config['sources'].append({"stream": address})
    else:
        config['sources'].append({"stream": addresses})

    headers = {'content-type': 'application/json'}
    response = requests.post(base_url+'/sources', data=json.dumps(config), headers=headers)
    if not response.ok:
        raise Exception('Unable to add input sources - '+response.text)


def get_input_sources():
    """

    Returns: Configured input sources of the dispatching layer - e.g. [{"stream":"tcp://localhost:9999"}]

    """
    response = requests.get(base_url+'/sources')

    if not response.ok:
        raise Exception('Unable to retrieve current input sources - ' + response.text)

    return response.json()


def remove_input_sources(addresses):
    """
    Remove input source from dispatching layer
    Args:
        addresses:

    Returns:

    """
    # Delete source
    config = {"sources": []}

    for address in addresses:
        config['sources'].append({"stream": address})

    headers = {'content-type': 'application/json'}
    response = requests.delete(base_url+'/sources', data=json.dumps(config), headers=headers)

    if not response.ok:
        raise Exception('Unable to delete input sources - ' + response.text)


if __name__ == '__main__':
    sources = get_input_sources()
    print(sources)


def request_stream(channels, stream_type='pub_sub'):
    """
    Request stream for specific channels
    Args:
        channels:   List of channels that should be in the stream. This is either a list of channel names and/or
                    a list of dictionaries specifying the desired channel configuration.
                    Example: ['ChannelA', {'name': 'ChannelC', 'modulo': 10},
                             {'name': 'ChannelC', 'modulo': 10, 'offset': 1}]
        stream_type: Type of stream, either pub_sub (default) or push_pull

    Returns: ZMQ endpoint to connect to for the stream

    """
    # Request stream
    config = {"channels": [], "streamType": stream_type, "sendIncompleteMessages": True}

    for channel in channels:
        if isinstance(channel, str):
            config['channels'].append({"name": channel})
        elif isinstance(channel, dict):
            # Ensure that we send an sane dictionary to the REST API
            channel_config = dict()
            channel_config['name'] = channel['name']
            if 'modulo' in channel:
                channel_config['modulo'] = channel['modulo']
            if 'offset' in channel:
                channel_config['offset'] = channel['offset']

            config['channels'].append(channel_config)

    logging.info('Request stream: ' + config.__str__())

    headers = {'content-type': 'application/json'}
    response = requests.post(base_url+'/stream', data=json.dumps(config), headers=headers)

    if not response.ok:
        raise Exception('Unable to request stream for specified channels - ' + response.text)

    logging.info('Stream returned: ' + response.text)

    return response.json()['stream']
    # TODO stream might contain more channels than the channels requested this library should filter these channels out.


def request_streams():
    """
    Get all streams currently served by the dispatching layer
    Returns:    List of streams

    """

    logging.info('Request currently available streams')
    # Get streams currently requested
    response = requests.get(base_url+'/streams')

    if not response.ok:
        raise Exception('Unable to retrieve current streams - ' + response.text)

    return response.json()


def remove_stream(stream):
    """
    Remove a stream currently served by the dispatching layer
    Args:
        stream:     url of stream to remove

    Returns:

    """

    logging.info('Remove stream: ' + stream)

    config = stream
    # TODO Update once the dispatching API was updated
    headers = {'content-type': 'application/json'}
    response = requests.delete(base_url+'/stream', data=json.dumps(config), headers=headers)

    if not response.ok:
        raise Exception('Unable to remove stream ' + stream + ' - ' + response.text)

    # config = "tcp://pineapple.psi.ch:50727"
    # headers = {'content-type': 'text/plain'}
    # response = requests.delete(base_url+'/stream', data=config, headers=headers)
