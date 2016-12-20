# Overview
This is a Python (>=3.5) package to deal with beam synchronous data. It is based on the streaming library [mflow](https://github.com/datastreaming/mflow) and provides the required message handlers to it.


__The bsread command line tools are based on this package. These commands are described in [ReadmeCLI.md](ReadmeCLI.md)__

The format of the bsread stream is specified [here](https://git.psi.ch/sf_daq/bsread_specification).

----

__Warning / Attention:__ Please ensure that you don't connect to a production IOC nor that you connect twice to a single IOC unless you are knowing what you are doing! Due to the current data delivery scheme (PUSH/PULL) data might be lost otherwise! If you are in doubt please ask for assistance from the Controls HA group.

----

# Usage

__Note:__ The bsread module, by default, accesses the SwissFEL Dispatching Layer. As this infrastructure is only accessible within the SwissFEL network the code needs to run on a machine that has direct access to this network.

You can get a customized, synchronized stream from any combination of beam synchronous channels by using this piece of code:

```python
with source(channels=['YOUR_CHANNEL', 'YOUR_SECOND_CHANNEL']) as stream:
    while True:
        message = stream.receive()
        print(message.data.data['YOUR_CHANNEL'].value)
```

If you want to request non 100Hz data for particular channels you can simply configure this as follows:

```python
with source(channels=['YOUR_CHANNEL', {'name': 'YOUR_SECOND_CHANNEL', 'modulo': '10', 'offset': 0}]) as stream:
    while True:
        message = stream.receive()
        print(message.data.data['YOUR_CHANNEL'].value)
```

As you can see you can mix simple channel names with specific channel configurations.


To receive beam synchronous data from a specific source without using the SwissFEL Dispatching Layer use:

```python
from bsread import source

with source(host='ioc', port=9999) as stream:
    # source.request(['TOCK-BSREAD:SIM-PULSE'])  # configure IOC
    while True:
        message = stream.receive()
        # Terminate loop at some time
```


In any case, the returned message object contains all information for one pulse. Following data is available.

```python
pulse_id = message.data.pulse_id
global_timestamp = message.data.global_timestamp
global_timestamp_offset = message.data.global_timestamp_offset
channel_value = message.data.data['channel_name']

# A channel value contains following information:
value = channel_value.value
timestamp = channel_value.timestamp
timestamp_offset = channel_value.timestamp_offset
```

The `message.data.data` dictionary is an [OrderedDict](https://docs.python.org/2/library/collections.html#collections.OrderedDict). Entries will always be sorted by the sequence they are added, i.e. the order will be the same as the order the channels are configured on the IOC.

Beside the actual data the message also includes statistics information. This information can be accessed by:

```
message.statistics
```

## Generating Streams
For various purposes (e.g. testing) beam synchronous streams can be easily created as follows:

```python
from bsread import Generator
generator = Generator()
# generator.set_pre_function(pre)
generator.add_channel('ABC', lambda x: x, metadata={'type': 'int32'})
generator.add_channel('ABCD', lambda x: x*10.0)
generator.add_channel('XYZW', lambda x: 'hello', metadata={'type': 'string'})
generator.add_channel('WWW', lambda x: [1.0, 2.0, 3.0, 4.0], metadata={'type': 'float64', 'shape': [4]})
# generator.set_post_function(pre)
generator.generate_stream()
```

The `add_channel` function is used to register functions to generate values for pulses. The registered functions need to accept one input parameter which will be filled with the pulse_id. The optional parameter for the `add_channel` function is metadata. As soon as the function does not return an float/double or the shape is not [1] the metadata needs to be set.

The constructor of `Generator()` accepts a parameter `block`, while specifying `block=False` the generator will drop messages incase the client is not able to keep up consuming the messages.

The generator also accepts a *pre* and a *post* function that will be called before sending the data (and before calling the lambdas) as well as after the sending.
This can be used, for example, to update an object that the registered lambdas are accessing.

To have the active loop in your code (instead of the Generator) you can

```python
from bsread import Generator
generator = Generator()
# generator.set_pre_function(pre)
generator.add_channel('ABC', lambda x: x, metadata={'type': 'int32'})

generator.open_stream()
while True:
    generator.send()
    time.sleep(0.01)

generator.close_stream()
```

A more complete example can be fount in [examples/generator.py](examples/generator.py).


Besides using lambdas for generating data you can also explicitly pass the data to send to the Generator. However, keep in mind that the then the active loop is in your domain. This can be done like this:

```python
from bsread import Generator
generator = Generator()
generator.add_channel('ABCD')
generator.add_channel('ABCD2')
generator.open_stream()
generator.send_data(1.0, 1.1)
generator.send_data(2.0, 2.1)
generator.close_stream()
```

An other way is to send data as follows:

```python 
from bsread import sender

with sender(queue_size=10) as stream:
    test_array = numpy.array([1, 2, 3, 4, 5, 6], dtype=numpy.uint16).reshape((2, 3))
    # Send Data
    stream.send(one=1, two=2,
                three=test_array)
    stream.send(pulse_id=0, one=3, two=4,
                three=test_array)
```

*Note:* The types and order of the data needs to correspond to the sequence the channels are registered. Also if a lambda was registered with a channel this lambda will be ignored.


# Installation

## Anaconda

The bsread package is available on [anaconda.org](https://anaconda.org/paulscherrerinstitute/bsread) and can be installed as follows:

```bash
conda install -c https://conda.anaconda.org/paulscherrerinstitute bsread
```


# Development

## Dependencies

The current dependencies are
* mflow
* [pyzmq](http://zeromq.github.io/pyzmq/)
* h5py
* numpy

A standard Anaconda distribution comes with all the required dependencies except mflow.

## Anaconda
To build the Anaconda package for this library

1. Update the version numbers in conda-recipe/meta.yaml
2. Create package: `conda build conda-recipe`
3. Upload package: `anaconda upload <path_to.tar.bz2_file>`
