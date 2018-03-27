
import zmq

context = zmq.Context()

tasks = context.socket(zmq.PUB)
tasks.bind('tcp://*:6555')

control = context.socket(zmq.PUB)
control.bind('tcp://*:6556')

check = context.socket(zmq.ROUTER)
check.bind('tcp://*:6557')


def start_workers(n):
    control.send(b'worker up please')
    for _ in range(n):
        ident, _, msg = check.recv_multipart()
        check.send_multipart([ident, b'', b'yes please'])
        print('started a worker')
    while True:
        try:
            ident, _, msg = check.recv_multipart()
            check.send_multipart([ident, b'', b'nope'])
            print('rejected a worker')
        except KeyboardInterrupt:
            return


def stop_workers(n):
    control.send(b'worker down please')
    for _ in range(n):
        ident, _, msg = check.recv_multipart()
        check.send_multipart([ident, b'', b'yes please'])
        print('stopped a worker')
    while True:
        try:
            ident, _, msg = check.recv_multipart()
            check.send_multipart([ident, b'', b'nope'])
            print('let a worker continue')
        except KeyboardInterrupt:
            return


import IPython

IPython.embed()

# This should be an async server which constantly listens
# on one thread to 'check' and responds to worker start/stop
# offers based on the desired state.
