''' Query system state, send control signals. '''

import IPython
import zmq

import protocol

context = zmq.Context()

controller_address = 'tcp://localhost:6000'

def client_send_recv(request):
    socket = context.socket(zmq.REQ)
    socket.connect(controller_address)
    socket.send(request)
    response = socket.recv()
    socket.close()
    return response

def state():
    request = protocol.msg_request_state()
    response = client_send_recv(request)
    return protocol.decode(response)

def shutdown(node):
    request = protocol.msg_request_shutdown(node)
    response = client_send_recv(request)
    return response

print('''
state()         -> Print the system state.
shutdown(node)  -> Signal the system to shut down.
''')

IPython.embed()
