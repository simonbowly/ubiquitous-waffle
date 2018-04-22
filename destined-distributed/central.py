
import datetime
import pprint

import msgpack
import zmq


node_state_address = 'tcp://*:6001'

context = zmq.Context()

node_state = context.socket(zmq.ROUTER)
node_state.bind(node_state_address)

state_data = {}

while True:
    waiting = node_state.poll(timeout=1000)
    now = datetime.datetime.now()
    if waiting:
        ident, message = node_state.recv_multipart()
        state_data[ident] = (now, msgpack.unpackb(message))
    state_data = {
        ident: (last_beat, message)
        for ident, (last_beat, message) in state_data.items()
        if (now - last_beat) <= datetime.timedelta(seconds=3)
    }
    pprint.pprint(state_data)
