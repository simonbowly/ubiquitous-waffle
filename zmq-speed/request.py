#!/usr/bin/env ipython

import click
import IPython
import zmq

@click.command()
@click.argument('count', default=1000)
@click.argument('port', default=6101)
def main(count, port):
    ''' Timing for REQ-REQ pattern. Must be run with ipython. '''

    address = f'tcp://*:{port:d}'
    context = zmq.Context()
    request = context.socket(zmq.REQ)
    request.bind(address)
    click.echo(f'REQ connected on:  {address}')

    def run(messages):
        for message in messages:
            request.send(message)
            assert request.recv() == message

    messages = [str(i).encode() for i in range(count)]
    click.echo(f'Testing with {count} messages.')
    run(messages)
    click.echo(f'Timing with {count} messages.')
    IPython.get_ipython().run_line_magic('timeit', '-n 10 run(messages)')

if __name__ == '__main__':
    main()
