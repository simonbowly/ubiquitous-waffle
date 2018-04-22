
import pprint
import time

import msgpack
import zmq


node_state_address = 'tcp://localhost:6001'
worker_state_address = 'tcp://*:6002'

context = zmq.Context()

# worker_control = context.socket(zmq.PUB)
# worker_control.bind()
worker_state = context.socket(zmq.SUB)
worker_state.setsockopt(zmq.SUBSCRIBE, b'')
worker_state.bind(worker_state_address)
node_state = context.socket(zmq.DEALER)
node_state.connect(node_state_address)


my_state = {
    'name': 'derby02',
    'state': 'running',
    'workers': {}}


while True:
    waiting = worker_state.poll(timeout=1000)
    if waiting:
        message = worker_state.recv()
        worker_info = msgpack.unpackb(message)
        my_state['workers'][worker_info[b'pid']] = worker_info
    node_state.send(msgpack.packb(my_state))
