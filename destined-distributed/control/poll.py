''' Query system state, send control signals. '''

from pprint import pprint
import time

import msgpack
import zmq

context = zmq.Context()

controller_address = 'tcp://localhost:6000'

socket = context.socket(zmq.REQ)
socket.connect(controller_address)

while True:
    request = msgpack.packb({'command': 'state'}, use_bin_type=True)
    socket.send(request)
    response = socket.recv()
    pprint(msgpack.unpackb(response, raw=False))
    time.sleep(1)
