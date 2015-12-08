# Overview
There are 2 utility command for bsread to facilitate and experiment with the beam synchronous data acquisition system.
The __bs-source__ command facilitates the easy setup of an test IOC as well as setting environment variables for specific iocs to allow easy usage of the __bs__ command. The __bs__ command provides easy to use receiving functionality to see and check whether an IOC is streaming out (correct) data. Also it provides an easy to use way to configure the channels that should be streamed out from an IOC.


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

### Example

```bash
bs-source create TOCK 7777

# To set the environment automatically use:
# eval "$(bs-source env sf-lc6-64 7777)"

export BS_SOURCE=tcp://sf-lc6-64:7777
export BS_CONFIG=tcp://sf-lc6-64:7778

# To start the test ioc use
iocsh startup.cmd
```

All the required commands are displayed to set your client environment as well as starting the test IOC.

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


```bash
Usage: bs [OPTIONS] COMMAND [arg...]

Commands:

 config          - Configure IOC
 stats           - Show receiving statistics
 receive         - Basic receiver
 h5              - Dump stream into HDF5 file

Run 'bs COMMAND --help' for more information on a command.
```
