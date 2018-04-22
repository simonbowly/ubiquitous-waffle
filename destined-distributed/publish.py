''' Load a task definition file and start broadcasting to anyone
who will listen. '''

import json
import random
import time

import msgpack
import zmq


context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:5600')


with open('task-defs.json') as infile:
    task_defs = json.load(infile)


encoded = msgpack.packb(task_defs, use_bin_type=True)


while True:
    time.sleep(1)
    print(f'Yelling with {len(task_defs)} tasks.')
    socket.send(encoded)
