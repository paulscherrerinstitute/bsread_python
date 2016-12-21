# Overview

To work and test with beam synchronous data sources there is the __bs__ command. The __bs__ command provides easy to use receiving functionality to see and check whether data is streamed correctly. There is also a sub-command that gives statistics about the incoming stream. Both can be used point to point to the source or via the SwissFEL dispatching layer.

Beside that the __bs__ command provides a way to configure the channels that should be streamed out from an IOC.

__Warning / Attention:__ Please ensure that you don't connect to a production source directly nor that you connect twice to a single source unless you are knowing what you are doing! Due to the current data delivery scheme (PUSH/PULL) data might be lost otherwise! If you are in doubt please ask for assistance from the Controls HA group (daq@psi.ch).

----

# bs

The __bs__ command provides some client side utilities to receive beam synchronous data from an IOC as well as configuring the IOC (which channels are recorded via bsread)

Therefore the command provides several subcommands with options.

```bash
Usage: bs [OPTIONS] COMMAND [arg...]

Commands:

 config          - Configure IOC
 stats           - Show receiving statistics
 receive         - Basic receiver
 h5              - Dump stream into HDF5 file
 create          - Create a test softioc
 simulate        - Provide a test stream

Run 'bs COMMAND --help' for more information on a command.
```

## bs receive

__bs receive__ can be used to receive and display bsread data from an IOC. If the client environment was set the __-s__ option can be omitted.

```bash
usage: receive [-h] [-s SOURCE] [-m] [channel [channel ...]]

bsread receive utility

positional arguments:
  channel               Channels to retrieve (from dispatching layer)

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source address - format "tcp://<address>:<port>"
  -m, --monitor         Monitor mode / clear the screen on every message
```

_Note:_ If `-s` is specified, the list of channels is ignored.

## bs stats

__bs stats__ provides you with some basic statistics about the messages received. Also a basic check whether pulse_ids were missing in the stream is performed.

```bash
usage: stats [-h] [-s SOURCE] [-m] [-n N] [-l LOG] [-v]
             [channel [channel ...]]

bsread statistics utility

positional arguments:
  channel               Channels to retrieve (from dispatching layer)

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        source address, has to be in format
                        "tcp://<address>:<port>"
  -m, --monitor         Enable monitor mode, this will clear the screen on
                        every message to allow easier monitoring.
  -n N                  Limit message printing to every n messages, this will
                        reduce CPU load. Note that all messages are still
                        received, but are not displayed. If -n 0 is passed
                        message display is disabled
  -l LOG, --log LOG     Enable logging. All errors (pulse_id skip, etc..) will
                        be logged in file specified
  -v, --value           Display values
```

_Note:_ If `-s` is specified, the list of channels is ignored.

## bs config
__bs config__ reads and updates the configuration a bsread enabled IOC.
While using no options it reads the current configuration from the IOC. While using `-u ` it generates and uploads a new configuration to the specified IOC. For the new configuration, the script reads from standard input. Therefore the input can also be piped into the program.

```
usage: config [-h] [-a] [-u] [-I INHIBIT] [-v] ioc

BSREAD configuration utility

positional arguments:
  ioc                   URL of config channel of ioc to retrieve config from

optional arguments:
  -h, --help            show this help message and exit
  -a, --all             Stream all channels of the IOC
  -u, --update          Update IOC configuration
  -I INHIBIT, --inhibit INHIBIT
                        Set inhibit bit
  -v, --verbose         Verbose output to show configuration json string
```

The script reads from standard input and terminates on EOF or empty lines

An input line looks like this:

```
<channel> modulo(optional, type=float ) offset(optional, type=int)
```

Note, that only the channel name is mandatory.

As mentioned before the configuration can also be piped from any other process. This is can be done like this:

```bash
echo -e "one\ntwo\nthree" | bs config -c <ioc> -u
```

## bs h5

__bs h5__ will dump the incoming stream into an hdf5 file for later analysis. As with the other commands, if the environment was set via `bs-source env` the __-s__ option can be omitted.

```bash
usage: h5 [-h] [-s SOURCE] file [channel [channel ...]]

BSREAD hdf5 utility

positional arguments:
  file                  Destination file
  channel               Channels to retrieve (from dispatching layer)

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source address - format "tcp://<address>:<port>"
```

__bs h5__ produces a very simple HDF5 structure. Each channel in the stream gets into a own group which holds the actual channel data, timestamp, timestamp_offset as well as the pulse_id of the channel.
data, timestamp, etc. within a channel group are arrays of the size of pulse_id/messages received.
The same index of the arrays corresponds to the same pulse_id which stored in the pulse_id dataset at the same index.


```
 IOC-TEST-FAKEDATA:TEST_WVF-DOUBLE
     timestamp [int64]
     data [float64]
     pulse_id [int64]
     timestamp_offset [int64]
 IOC-TEST-FAKEDATA:TEST_WVF-INT
     timestamp [int64]
     data [int32]
     pulse_id [int64]
     timestamp_offset [int64]
```

_Note:_ If `-s` is specified, the list of channels is ignored.

# bs simulate

To generate a test stream use:

```
bs simulate
```

Usage:

```bash
usage: simulate [-h] [-p PORT]

bsread simulation utility

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Port number of stream
```

# bs create

To create the configuration of a test softioc use:

```bash
bs create MY-PREFIX 7777
```

The first argument is the prefix for the test records as well as IOC name, the second needs to be a random port - especially when setting up a test IOC on the login cluster nodes. If the port is omitted, the default port 9999 is taken (the standard bsread port). However this port should only be used if you are sure your test ioc is the only IOC of the node running it.

```bash
usage: create [-h] [--db DB] prefix port

bsread create utility - creates a sample ioc configuration

positional arguments:
  prefix      ioc prefix
  port        ioc stream port

optional arguments:
  -h, --help  show this help message and exit
  --db DB     create additional test database with specified number of scalars
              and waveforms using generator strings (e.g.
              'scalar(10);waveform(10,1024)') input commands must be delimited
              with ';'. Available input commands: scalar([no of scalars])
              waveform([no of waveforms],[size of waveform])
```

After creating the configuration files with the command use `iocsh startup.cmd` to start the IOC.

The creation and start of the test ioc can be done in one go with following command:

```bash
eval "$(bs create TOCK 7777)"
```
