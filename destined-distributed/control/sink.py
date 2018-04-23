
import zmq

import protocol


context = zmq.Context()
sink = context.socket(zmq.PULL)
sink.bind('tcp://*:6010')

while True:
    message = sink.recv()
    print(protocol.decode(message))
