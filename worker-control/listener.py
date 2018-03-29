
import random
import time

import zmq

context = zmq.Context()

sub = context.socket(zmq.SUB)
sub.connect('tcp://localhost:5555')
sub.setsockopt(zmq.SUBSCRIBE, b'')

req = context.socket(zmq.REQ)
req.connect('tcp://localhost:5557')

while True:
    # In reality this should fast forward to the latest message.
    msg = sub.recv()
    print(f'SUB: {msg}')
    time.sleep(0.5)
    if random.random() < 0.5:
        print('Sending offer_start')
        req.send(b'offer_start')
    else:
        print('Sending offer_stop')
        req.send(b'offer_stop')
    print(f'REP: {req.recv()}')
