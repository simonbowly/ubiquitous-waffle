#!/usr/bin/env python

import click
import zmq

@click.command()
@click.argument('host', default='localhost')
@click.argument('port', default=6101)
def main(host, port):
    ''' REP socket which echoes messages forever. '''

    address = f'tcp://{host:s}:{port:d}'
    context = zmq.Context()
    reply = context.socket(zmq.REP)
    reply.connect(address)
    click.echo(f'REP connected to:  {address}')

    while True:
        message = reply.recv()
        reply.send(message)

if __name__ == '__main__':
    main()
