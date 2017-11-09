# Overview
This Documentation is for internal use only. It describes functionality that must only be used by 'pro' users.

# Usage

## Update TTL Of Data
Following code can be used to update the time to live of data inside the DataBuffer.

```python
from bsread import dispatcher
import datetime

channels = ["CHAN_A", "CHAN_B"]
ttl = datetime.timedelta(weeks=1)  # keep data for 1 week

timestamp = datetime.datetime.now()
start = timestamp - datetime.timedelta(seconds=1)  # keep 1 second worth of data before now
end = timestamp + datetime.timedelta(seconds=0.1)  # 1 second safety margin

dispatcher.update_ttl(channels, start, end, ttl)
```
