import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:5602')

for i in range(10):
    print(f'Shutting down in {10-i} ...')
    time.sleep(1)

socket.send(b'shutdown')
