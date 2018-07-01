''' Query system state, send control signals. '''

import click
import IPython
import zmq

import protocol

context = zmq.Context()

controller_address = 'tcp://192.168.1.106:6000'


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

def shutdown_node(node):
    request = protocol.msg_request_shutdown(node)
    response = client_send_recv(request)
    return response


@click.group()
def cli():
    pass


@cli.command()
def interact():

    print('''
    state()         -> Print the system state.
    shutdown(node)  -> Signal the system to shut down.
    ''')

    IPython.embed()


@cli.command()
def shutdown():
    click.echo({node['name']: shutdown_node(_id) for _id, node in state()['nodes'].items()})


if __name__ == '__main__':
    cli()
