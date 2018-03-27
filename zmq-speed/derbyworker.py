
import time

import zmq

context = zmq.Context()

tasks = context.socket(zmq.SUB)
tasks.connect('tcp://localhost:6555')
tasks.setsockopt(zmq.SUBSCRIBE, b'')
# could use setsockopt for topics instead
control = context.socket(zmq.SUB)
control.connect('tcp://localhost:6556')
control.setsockopt(zmq.SUBSCRIBE, b'')

check = context.socket(zmq.REQ)
check.connect('tcp://localhost:6557')

# for latest-is-true subscriber sockets
poller = zmq.Poller()
poller.register(tasks, zmq.POLLIN)
poller.register(control, zmq.POLLIN)

def check_latest(socket):
    message = None
    while socket in dict(poller.poll(timeout=0)):
        message = socket.recv()
    return message

state_message = None

while True:

    # Waiting to go up from idle.
    while True:
        if control.recv() == b'worker up please':
            print('someone wants a new worker...')
            check.send(b'offer start')
            if check.recv() == b'yes please':
                print('yay i get to start!')
                break
            else:
                print('unwanted...')

    # Start listening for work changes or shutdown signal.
    while True:
        control_message = check_latest(control)
        if control_message == b'worker down please':
            print('stop requested')
            check.send(b'offer stop')
            if check.recv() == b'yes please':
                print('going down')
                break
            else:
                print('continuing...')
        state_message = check_latest(tasks) or state_message
        print(f'Doing work for task "{state_message}"')
        time.sleep(1)
