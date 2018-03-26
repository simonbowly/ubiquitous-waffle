#!/usr/bin/env ipython

import click
import IPython
import zmq

@click.command()
@click.argument('count', default=1000)
@click.argument('source-port', default=6102)
@click.argument('sink-port', default=6103)
def main(count, source_port, sink_port):
    ''' Timing for PUSH-PUL pattern. Must be run with ipython. '''

    ventilate_address = f'tcp://*:{source_port:d}'
    sink_address = f'tcp://*:{sink_port:d}'
    context = zmq.Context()
    ventilator = context.socket(zmq.PUSH)
    ventilator.bind(ventilate_address)
    sink = context.socket(zmq.PULL)
    sink.bind(sink_address)
    click.echo(f'PUSH ventilating on:  {ventilate_address}')
    click.echo(f'PULL collecting on:   {sink_address}')

    def run(messages):
        for message in messages:
            ventilator.send(message)
        for message in messages:
            assert sink.recv() == message

    messages = [str(i).encode() for i in range(count)]
    run(messages)
    click.echo(f'Running with {count} messages.')
    IPython.get_ipython().run_line_magic('timeit', '-n 10 run(messages)')

if __name__ == '__main__':
    main()
