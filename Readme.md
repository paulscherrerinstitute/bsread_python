# Overview
Python utility classes for working with BSREAD. 
It offers an easy way to receive an BSREAD stream as well as simulating an BSREAD source - `bsread_receiver.py` 
and `bsread_sender.py` are some simple examples.

The format of the stream is specified
[here](https://docs.google.com/document/d/1BynCjz5Ax-onDW0y8PVQnYmSssb6fAyHkdDl1zh21yY/edit#heading=h.ugxijco36cap).

# Scripts

## bsread_client.py
Utility script to generate and upload a BSREAD ioc configuration. The script reads from standard input.
Therefore input can also be piped into the program.

Usage:

```
python bsread_client.py [ioc]
```

The script reads from standard input and terminates on EOF or empty lines

An input line looks like this:

```
<channel> frequency(optional, type=float ) offset(optional, type=int)
```

Note that only the channel name is mandatory.

Configuration can also be piped from any other process. This is done like this:

```bash
echo -e "one\ntwo\nthree" | python bsread_client.py
```
    
## bsread_util.py

simple receiver that operates similar to camon. Script can be used to verify correct operation of bsread senders. 

### Example usage

Confirm that all received bsread packates have monotonically increasing BunchID number: 

		bsread_util.py tcp://localhost:9991 -n 10 -l test.log

Above command will connect to BSREAD server on localhost on port 9991 (default for IOCs is 9999) and will display contents of every 10nth message (-n 10) and log any anomalies into a log file test.log (-l test.log)


### Built in help

		usage: bsread_util.py [-h] [-m] [-n N] [-l LOG] address

		BSREAD receiving utility

		positional arguments:
		  address            source address, has to be in formatP
		                     "tcp://<address>:<port>"

		optional arguments:
		  -h, --help         show this help message and exit
		  -m, --monitor      Enable monitor mode, this will clear the screen on every
		                     message to allow easier monitoring.
		  -n N               Limit message priniting to every n messages, this will
		                     reduce CPU load. Note that all messages are still
		                     recevied, but are not displayed. If -n 0 is passed
		                     message display is disabled
		  -l LOG, --log LOG  Enable logging. All errors (BunchID cnt skip, etc..) will
		                     be logged in file specifed




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

