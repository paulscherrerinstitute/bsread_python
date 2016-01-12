# Overview
This is a Python (3) package to deal with beam synchronous data. It is based on the base streaming library mflow and just provides the required message handlers to it.

The bsread command line tools are based on this package. If you are looking for those please consult the https://git.psi.ch/sf_daq/bsread_commandline documentation.

The format of the bsread stream is specified [here](https://docs.google.com/document/d/1BynCjz5Ax-onDW0y8PVQnYmSssb6fAyHkdDl1zh21yY/edit#heading=h.ugxijco36cap).

----

__Warning / Attention:__ Please ensure that you don't connect to a production IOC nor that you connect twice to a single IOC unless you are knowing what you are doing! Due to the current data delivery scheme (PUSH/PULL) data might be lost otherwise! If you are in doubt please ask for assistance from the Controls HA group.

----

# Usage

Following code can be used to receive beam synchronous data from a source.

```python
import mflow
import bsread.handlers.compact import Handler

receiver = mflow.connect(source, conn_type="connect", mode=zmq.PULL)
handler = Handler()

while True:
    message = receiver.receive(handler=handler.receive)
```

The returned message object contains all information for one pulse. Following data is available.

```python
pulse_id = message.pulse_id
global_timestamp = message.global_timestamp
global_timestamp_offset = message.global_timestamp_offset
channel_value = message.data['channel_name']

value = channel_value.value
timestamp = channel_value.timestamp
timestamp_offset = channel_value.timestamp_offset
```

The `message.data` dictionary is an [OrderedDict](https://docs.python.org/2/library/collections.html#collections.OrderedDict). Entries will always be sorted by the sequence they are added, i.e. the order will be the same as the order the channels are configured on the IOC.

# Development

## Dependencies

The current dependencies are
* mflow
* [pyzmq](http://zeromq.github.io/pyzmq/)
* h5py
* numpy

A standard Anaconda distribution comes with all the required dependencies except mflow.

## Build
To build the Anaconda package for this library

1. Update the version numbers in conda-recipe/bsread/meta.yaml
2. Go to conda-recipe
3. conda build bsread
