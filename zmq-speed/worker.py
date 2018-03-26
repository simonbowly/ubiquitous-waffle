#!/usr/bin/env python

import click
import zmq

@click.command()
@click.argument('host', default='localhost')
@click.argument('source-port', default=6102)
@click.argument('sink-port', default=6103)
def main(host, source_port, sink_port):
    ''' PULL-PUSH worker which passes on messages forever. '''

    pull_address = f'tcp://{host:s}:{source_port:d}'
    push_address = f'tcp://{host:s}:{sink_port:d}'
    context = zmq.Context()
    pull = context.socket(zmq.PULL)
    pull.connect(pull_address)
    push = context.socket(zmq.PUSH)
    push.connect(push_address)
    click.echo(f'PULL connected to source:  {pull_address}')
    click.echo(f'PUSH connected to sink:    {push_address}')

    while True:
        message = pull.recv()
        push.send(message)

if __name__ == '__main__':
    main()
