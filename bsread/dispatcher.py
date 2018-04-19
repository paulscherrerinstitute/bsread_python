import requests
import json

import logging
import datetime

base_url = 'http://localhost:8080'
base_url = 'https://dispatcher-api.psi.ch/sf'


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
    """ Returns: Configured input sources of the dispatching layer - e.g. [{"stream":"tcp://localhost:9999"}] """
    response = requests.get(base_url+'/sources')

    if not response.ok:
        raise Exception('Unable to retrieve current input sources - ' + response.text)

    return response.json()


def get_current_channels():
    """ Get current incoming channels """
    response = requests.get(base_url + '/channels/live')

    if not response.ok:
        raise Exception('Unable to retrieve current incoming channels - ' + response.text)

    channel_list = []
    for backend in response.json():
        channel_list.extend(backend['channels'])
    return channel_list


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


def request_stream(channels, stream_type='pub_sub', inconsistency_resolution="adjust-individual", verify=True):
    """
    Request stream for specific channels
    Args:
        channels:                   List of channels that should be in the stream. This is either a list of channel
                                    names and/or a list of dictionaries specifying the desired channel configuration.
                                    Example: ['ChannelA', {'name': 'ChannelC', 'modulo': 10},
                                             {'name': 'ChannelC', 'modulo': 10, 'offset': 1}]
        stream_type:                Type of stream, either pub_sub (default) or push_pull
        inconsistency_resolution:   How to resolve inconsistencies in frequencies of the requested channels
                                    See: https://git.psi.ch/sf_daq/ch.psi.daq.dispatcherrest#channel-validation
                                    values: adjust-individual, keep-as-is
        verify:                     Check whether all channels are currently available and connected. Checks for 
                                    frequencies, etc. . If false inconsistency_resolution will be set to keep-as-is

    Returns: ZMQ endpoint to connect to for the stream

    """

    if not verify:
        logging.debug("Set inconsistency_resolution to 'keep-as-is' ")
        inconsistency_resolution = "keep-as-is"

    # Request stream
    config = {"channels": [],
              "streamType": stream_type,
              "verify": verify,
              "channelValidation": {"inconsistency": inconsistency_resolution}}

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

    headers = {'content-type': 'text/plain'}
    response = requests.delete(base_url+'/stream', data=stream, headers=headers)

    if not response.ok:
        raise Exception('Unable to remove stream ' + stream + ' - ' + response.text)


def get_data_policies():
    logging.info('Request currently configured data policies')
    response = requests.get(base_url + '/data/policies')

    if not response.ok:
        raise Exception('Unable to retrieve current data policies - ' + response.text)

    return response.json


def update_time_to_live(channels, start, end, ttl: datetime.timedelta, async=True):
    update_ttl(channels, start, end, ttl, async=async)


def update_ttl(channels, start, end, ttl: datetime.timedelta, async=True):
    """
    Update the ttl of specific data:
    https://git.psi.ch/sf_daq/ch.psi.daq.dispatcherrest#update-ttl
    
    :param start:  Start of range to update = either datetime or pulse_id
    :param end: End of range to update - either datetime or pulse_id
    :param channels: List of channels to update ttl
    :param ttl: Time to live as datatime.timedelta 
    :param async: Execute call asynchronously
    
    
    :return: 
    """

    if not isinstance(ttl, datetime.timedelta):
        raise RuntimeError('Invalid ttl - need to be of type timedelta')

    update_request = {
        "ttl": int(ttl.total_seconds()),  # Value need to be a long
        "asyncCall": async,
        "channels": [],
        "range": {}
    }

    channel_list = []
    for channel in channels:
        if channel.startswith("sf-databuffer/"):
            channel_list.append({"name": channel.replace("sf-databuffer/", ""), "backend": "sf-databuffer"})
        elif channel.startswith("sf-archiverappliance/"):
            channel_list.append(
                {"name": channel.replace("sf-archiverappliance/", ""), "backend": "sf-archiverappliance"})
        else:
            channel_list.append({"name": channel, "backend": "sf-databuffer"})
    update_request["channels"] = channel_list

    if isinstance(start, int) and isinstance(end, int):
        update_request["range"] = {"startPulseId": start,
                                   "endPulseId": end}
    elif isinstance(start, datetime.datetime) and isinstance(end, datetime.datetime):
        update_request["range"] = {"startDate": start.isoformat(),
                                   "endDate": end.isoformat()}
    else:
        raise RuntimeError("Invalid start and/or end time/pulse_id")

    logging.debug("Update TTL Request:\n" + json.dumps(update_request))

    headers = {'content-type': 'application/json'}
    response = requests.post(base_url + '/data/update/ttl', data=json.dumps(update_request), headers=headers)

    if not response.ok:
        raise Exception('Unable to update ttl for specified channels - ' + response.text)

    _log_ttl_update_info_to_central_server(channels, start, end, ttl)


def _log_ttl_update_info_to_central_server(channels, start, end, ttl):
    """
    Logging function to central logstash server to keep track of who is updating what ttl (which channels, what ttl)

    :param channels:
    :param start:
    :param end:
    :param ttl:
    :return:

    """
    import socket
    import getpass
    import json
    from threading import Thread

    log_message = "%s - %s - %s - %s" % (channels, start, end, ttl)

    def send_info(message):
        HOST = 'logstash.psi.ch'
        PORT = 5678

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect((HOST, PORT))

            msg = {'message': message, 'tags': ['python', 'library'], 'operation': 'update ttl',
                   'username': getpass.getuser(), 'hostname': socket.gethostname()}
            sock.send(json.dumps(msg).encode())

        except socket.error:
            print('error')
            pass

        finally:
            try:
                sock.close()
            except:
                pass

    thread = Thread(target=send_info, args=(log_message,))
    thread.start()
