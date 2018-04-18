
import random
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:5600')

time.sleep(1)

socket.send(b'idle')

time.sleep(1)
