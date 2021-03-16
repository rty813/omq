# omq

Omq is a IPC that uses [Nanomsg](https://nanomsg.org/) under the hood. It likes MQTT in some degree.

### Concept
nanomsg is a socket library that provides several common communication patterns. It aims to make the networking layer fast, scalable, and easy to use. Implemented in C, it works on a wide range of operating systems with no further dependencies. But its sub-pub mode is not very good for us to use. So, omq bornd. Through omq, you can easily publish and subscribe message like MQTT.

## Installation
```
% wget https://github.com/nanomsg/nanomsg/archive/1.1.5.tar.gz
% tar -xvzf 1.1.5.tar.gz
% cd nanomsg-1.1.5
% mkdir build
% cd build
% cmake ..
% cmake --build .
% ctest .
% sudo cmake --build . --target install
% sudo ldconfig

% pip install omq
```

Omq requires python 3.6+

## Usage

Omq implements Broker and Socket. Before publish and subscribe, you need to start a broker at first.


### Basic

```python
# node1.py
import omq

with omq.Bus() as node:
    node.publish('test', 'hello world')
```


```python
# node2.py
import omq

def on_message(topic, payload):
    print(f'{topic} - {payload}')

with omq.Bus() as node:
    node.on_message = on_message
    node.subscribe(['test', 'test/#'])
    node.loop_forever()
```