
import zmq

context = zmq.Context()
sink = context.socket(zmq.PULL)
sink.bind('tcp://*:6010')

while True:
    message = sink.recv()
    print(message)
