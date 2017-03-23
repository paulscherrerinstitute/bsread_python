# Overview
The bsread Python package can also be used from within Matlab to receive beam synchronous data. As the Python integration in Matlab does not allow key based parameters in function calls, there are some small caveats needed to make it working.

# Usage

Before starting Matlab from the Command Line, make sure you have the proper Python in your path.

```Bash
source /opt/gfa/python
```

Afterwards start Matlab from the very same Command Line.

To be able to use the package you have to place following Python file into your project:

```Python
from bsread import Source as SourceOriginal
from bsread import SUB

class Source(SourceOriginal):

   def __init__(self, channel_names):
       super().__init__(channels=channel_names, mode=SUB, dispatcher_url='http://dispatcher-api.psi.ch/sf')
```

You can have a arbitrary filename but we recommend to name the file `bs.py` so that you can just copy the examples given below.

To receive beam synchronous data you can use this piece of code:

```Matlab
stream = py.bs.Source({'SLG-LSCP1-FNS:CH0:VAL_GET'})
stream.connect()

% for i = 1:10
message = stream.receive()
message.data.data{'SLG-LSCP1-FNS:CH0:VAL_GET'}.value
% end

stream.disconnect()
```

The received message has following structure and metadata

```Matlab
pulse_id = message.data.pulse_id
global_timestamp = message.data.global_timestamp
global_timestamp_offset = message.data.global_timestamp_offset
channel_value = message.data.data{'channel_name'}

# A channel value contains following information:
value = channel_value.value
timestamp = channel_value.timestamp
timestamp_offset = channel_value.timestamp_offset
```
