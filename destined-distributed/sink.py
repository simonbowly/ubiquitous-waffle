import msgpack
import zmq

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://*:5601')

i = 1
while True:
    message = socket.recv()
    result = msgpack.unpackb(message)
    print(f'Result {i}', result)
    i = i + 1
