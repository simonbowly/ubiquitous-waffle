''' Query system state, send control signals. '''

from pprint import pprint

import IPython
import msgpack
import zmq

context = zmq.Context()

controller_address = 'tcp://localhost:6000'

def state():
    request = msgpack.packb({'command': 'state'}, use_bin_type=True)
    socket = context.socket(zmq.REQ)
    socket.connect(controller_address)
    socket.send(request)
    message = socket.recv()
    socket.close()
    return msgpack.unpackb(message, raw=False)

def shutdown(node):
    request = msgpack.packb({'command': 'shutdown', 'node': node}, use_bin_type=True)
    socket = context.socket(zmq.REQ)
    socket.connect(controller_address)
    socket.send(request)
    message = socket.recv()
    socket.close()
    return message

print('''
state()         -> Print the system state.
shutdown(node)  -> Signal the system to shut down.
''')

IPython.embed()
