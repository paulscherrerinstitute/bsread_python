# Overview
Python utility classes for working with BSREAD. 
It offers an easy way to receive an BSREAD stream as well as simulating an BSREAD source - `bsread_receiver.py` 
and `bsread_sender.py` are some simple examples.

The format of the stream is specified
[here](https://docs.google.com/document/d/1BynCjz5Ax-onDW0y8PVQnYmSssb6fAyHkdDl1zh21yY/edit#heading=h.ugxijco36cap).

# Scripts
## bsread_sender.py
Example BSREAD source. By starting the script via `python bsread_sender.py` you will generate a BSREAD data source serving
specification compliant data stream.

## bsread_receiver.py
This script dumps all messages received from a BSREAD stream to standard out. The usage is as follows:

```
receiver.py -s <source> -f <output_file>
```

The _source_ parameter is specified as this: `tcp://localhost:9999` (default value)


## receiver.py
Receive and write BSREAD data into a HDF5 file. The usage is as follows:

```
receiver.py -s <source> -f <output_file>
```

The _source_ parameter is specified as this: `tcp://localhost:9999` (default value)

# Dependencies

* Python 2.7
* [pyzmq](http://zeromq.github.io/pyzmq/)

Optional
* [cachannel](https://bitbucket.org/xwang/cachannel/src/d8cba8b4b525e960497f539f92a7481cc1ab99e3?at=default) 2.4.0

*This code just runs fine in an [Anaconda](http://continuum.io/downloads) environment if you don't need the bsread configuration scripts.
 Otherwise you also have to install cachannel from the PSI anaconda repository*

## Anaconda

If this is the initial checkout of this project create an Anaconda environment for the project

```
conda create --yes -n bsread anaconda
```

To activate this environment, use:

```
source activate bsread
```

To deactivate this environment, use:

```
source deactivate
```

