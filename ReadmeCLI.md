# Overview
There are 2 utility command for bsread to facilitate and experiment with the beam synchronous data acquisition system.
The __bs-source__ command facilitates the easy setup of an test IOC as well as setting environment variables for specific iocs to allow easy usage of the __bs__ command. The __bs__ command provides easy to use receiving functionality to see and check whether an IOC is streaming out (correct) data. Also it provides an easy to use way to configure the channels that should be streamed out from an IOC.

The format of the stream is specified [here](https://docs.google.com/document/d/1BynCjz5Ax-onDW0y8PVQnYmSssb6fAyHkdDl1zh21yY/edit#heading=h.ugxijco36cap).

----

__Note:__ For the time being, to be able to use the commands from GFA machines you need to add the central GFA Python environment to you path. This can be done by executing following command:

```
source /opt/gfa/python
```

----

__Warning / Attention:__ Please ensure that you don't connect to a production IOC nor that you connect twice to a single IOC unless you are knowing what you are doing! Due to the current data delivery scheme (PUSH/PULL) data might be lost otherwise! If you are in doubt please ask for assistance from the Controls HA group (daq@psi.ch).

----

# bs-source
__bs-source__ provides an easy way to create a test IOC for testing as well as setting environment variables that facilitates the usage of the __bs__ command.

The usage of __bs-source__ is as follows:

```bash
Usage: bs-source [-h] {create,env,clear_env} ...

bsread source utility

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  Subcommands

  {create,env,clear_env}
                        additional help
    create              Create configuration files for a test ioc
    env                 Display environment variable for easy use of bs
                        command
    clear_env           Display how to clear environment variables
```

## Generate Test Stream

To generate a test stream use:

```
bs-source run
```

Usage:

```bash
usage: bs-source run [-h] [port]

positional arguments:
  port        port number of stream

optional arguments:
  -h, --help  show this help message and exit
```

## Create a Test IOC

To create the configuration of a test IOC simply use:

```bash
bs-source create MY-PREFIX 7777
```

The first argument is the prefix for the test records as well as IOC name, the second needs to be a random port - especially when setting up a test IOC on the login cluster nodes. If the port is omitted, the default port 9999 is taken (the standard bsread port). However this port should only be used if you are sure your test ioc is the only IOC of the node running it.

```bash
bs-source create -h
usage: bs-source create [-h] prefix port

positional arguments:
  prefix      ioc prefix
  port        ioc stream port

optional arguments:
  -h, --help  show this help message and exit
```

After creating the configuration files with the command use `iocsh startup.cmd` to start the IOC. All the required commands are displayed to set your client environment as well as starting the test IOC.


The creation and start of the test ioc can be done in one go with following command:

```bash
eval "$(bs-source create TOCK 7777)"
```



## Set environment

To set the client side environment for easy __bs__ command usage you can use

```bash
bs-source env -h
usage: bs-source env [-h] ioc [port]

positional arguments:
  ioc         ioc name
  port        port number of stream

optional arguments:
  -h, --help  show this help message and exit
```

If the command is executed the environment settings are just displayed. To also set environment follow the instructions shown at the start of the output.

### Example

```bash
bs-source env sf-lc 9999

# To set the environment automatically use:
# eval "$(bs-source env sf-lc 9999)"

export BS_SOURCE=tcp://sf-lc:9999
export BS_CONFIG=tcp://sf-lc:10000
```

As mentioned before to also set the environment use the command displayed at the beginning of the output:

```bash
eval "$(bs-source env sf-lc 9999)"
```

## Clear environment

To clear the client side environment use:

```bash
bs-source clear_env -h
usage: bs-source clear_env [-h]

optional arguments:
  -h, --help  show this help message and exit
```

The command just displayed the commands needed to clear the client side environment. To also set environment follow the instructions shown at the start of the output.

### Example
```
bs-source clear_env

# To unset the environment use:
# eval "$(bs-source clear_env)"
unset BS_SOURCE
unset BS_CONFIG
```

To immediately unset the environment without copy/paste the output use

```bash
eval "$(bs-source clear_env)"
```

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

Run 'bs COMMAND --help' for more information on a command.
```

## bs config
__bs config__ reads and updates the configuration a bsread enabled IOC.
While using no options it reads the current configuration from the IOC. While using `-u ` it generates and uploads a new configuration to the specified IOC. For the new configuraiton, the script reads from standard input. Therefore the input can also be piped into the program.

```
config [-h] [-c CHANNEL] [-a] [-i] [-I INHIBIT] [-v]

BSREAD configuration utility

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNEL, --channel CHANNEL
                        Address to configure, has to be in format
                        "tcp://<address>:<port>"
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

Note that only the channel name is mandatory.

If the client side environment was not set via the `bs-source env` command you have to specify the IOC configuration channel via the __-c__ option. If the environment was set this option can be omitted.
__Note:__ The configuration channel port is the ONE port above the data port. i.e. if the data port is 9999 the configuration port is 10000.


As mentioned before the configuration can also be piped from any other process. This is can be done like this:

```bash
echo -e "one\ntwo\nthree" | bs config -c tcp://<ioc>:<port> -u
```

or

```bash
cat myconfig | bs config -u
```

__Note:__ In the last example the environment was set via `bs-source env`

## bs receive

__bs receive__ can be used to receive and display bsread data from an IOC. If the client environment was set the __-s__ option can be omitted.

```bash
usage: receive [-h] [-s SOURCE] [-m]

BSREAD receive utility

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source address - format "tcp://<address>:<port>"
  -m, --monitor         Monitor mode / clear the screen on every message
```

## bs stats

__bs stats -m__ provides you with some basic statistics about the messages received. Also a basic check whether pulse_ids were missing in the stream is performed.

```bash
usage: stats [-h] [-s SOURCE] [-m] [-n N] [-l LOG] [-v]

bsread statistics utility

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

## bs h5

__bs h5__ will dump the incoming stream into an hdf5 file for later analysis. As with the other commands, if the environment was set via `bs-source env` the __-s__ option can be omitted.

```bash
usage: h5 [-h] [-s SOURCE] file

BSREAD hdf5 utility

positional arguments:
  file                  Destination file

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

### Matlab
The saved hdf5 file can be read / browsed within Matlab as follows:

```Matlab
% Show content/structure of hdf5 file
h5disp('data.h5')

% Get file info to visually browse the content/structure
hdf5info('data.h5')

% Read data
data = hdf5read('data.h5', '/MINSB04-RLLE-RFRX:CH2-AMPLT/data')
```

# Development
The bsread commandline is based on the bsread Python library (https://git.psi.ch/sf_daq/bsread_python). Please check the documentation of this package regarding development, packaging and deployment.
