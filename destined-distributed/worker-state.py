
import os
import random
import time

import msgpack
import zmq


worker_state_address = 'tcp://localhost:6002'

context = zmq.Context()

worker_state = context.socket(zmq.PUB)
worker_state.connect(worker_state_address)


while True:
    time.sleep(random.randint(2, 4))
    worker_state.send(msgpack.packb({
        'pid': os.getpid(),
        'state': random.choice(['running', 'idle'])
        }))
