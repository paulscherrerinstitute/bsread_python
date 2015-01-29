# Overview
Python utility classes for working with BSREAD. 
It offers am easy way to receive an BSREAD stream as well as simulating an BSREAD source.

The format of the streams are specified
[here](https://docs.google.com/document/d/1BynCjz5Ax-onDW0y8PVQnYmSssb6fAyHkdDl1zh21yY/edit#heading=h.ugxijco36cap).

# Examples

## Receive a Stream

```python
import bsread
import zmq

bsread = bsread.Bsread(mode=zmq.PULL)
bsread.connect(address="tcp://localhost:9999", conn_type="connect", )
while True:
    bsread.receive()
    print "----"
```

## BSREAD Source

```python
import bsread
import zmq

bsread = bsread.Bsread(mode=zmq.PUSH)
bsread.connect(address="tcp://*:9999", conn_type="bind", )
bsread.send()
```





Example Python scripts to show how to receive data from bsread as well as an simulator of bsread (i.e. for testing purposes).
