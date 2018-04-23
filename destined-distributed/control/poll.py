''' Query system state, send control signals. '''

from pprint import pprint
import time

import zmq

import protocol


context = zmq.Context()

controller_address = 'tcp://localhost:6000'

socket = context.socket(zmq.REQ)
socket.connect(controller_address)

while True:
    socket.send(protocol.msg_request_state())
    response = socket.recv()
    pprint(protocol.decode(response))
    time.sleep(1)
