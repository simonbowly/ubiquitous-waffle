
import logging
import random
import time

import click
import zmq

import protocol


def get_latest_waiting(socket, default=None):
    ''' Return the latest waiting message on :socket, or :default if
    no messages waiting. Earlier messages are discarded. This function
    is non-blocking; :socket is polled with zero timeout. '''
    message = default
    while True:
        if socket.poll(timeout=0) == 0:
            break
        message = socket.recv()
    return message


@click.command()
@click.option(
    '--tasks-address', default='tcp://localhost:6002',
    help='Subscribe for task definitions.')
@click.option(
    '--shutdown-address', default='tcp://localhost:6003',
    help='Listen for shutdown signal.')
@click.option(
    '--sink-address', default='tcp://localhost:6010',
    help='Push results.')
@click.option('--log-file', default=None)
def worker(tasks_address, shutdown_address, sink_address, log_file):
    ''' Launch a worker process which completes tasks and pushes the results
    until signalled to shutdown. '''

    if log_file:
        logging.basicConfig(filename=log_file, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    context = zmq.Context()
    # PUB-SUB connection to receive latest task definitions.
    tasks = context.socket(zmq.SUB)
    tasks.setsockopt(zmq.SUBSCRIBE, b'')
    tasks.connect(tasks_address)
    # PUB-SUB connection to receive a shutdown signal.
    shutdown = context.socket(zmq.SUB)
    shutdown.setsockopt(zmq.SUBSCRIBE, b'')
    shutdown.connect(shutdown_address)
    # PUSH-PULL channel to send results of completed tasks. Linger is set on
    # this socket; if the worker is shut down, undelivered results will be
    # discarded after this time expires.
    sink = context.socket(zmq.PUSH)
    sink.connect(sink_address)
    sink.setsockopt(zmq.LINGER, 10000)
    # Poller used when worker is waiting for a task definition.
    poller = zmq.Poller()
    poller.register(tasks, zmq.POLLIN)
    poller.register(shutdown, zmq.POLLIN)

    logging.info(f'Listening for tasks on {tasks_address}')
    logging.info(f'Listening for shutdown on {shutdown_address}')
    logging.info(f'Pushing results to {sink_address}')

    current_task = b'0'
    while True:
        # Any waiting message on this socket is interpreted as a shutdown.
        if shutdown.poll(timeout=0):
            logging.info('Shutting down')
            break
        # Fast forward to the most recent message.
        current_task = get_latest_waiting(tasks, default=current_task)
        # If current task is the the default no-work signal, block the worker
        # until another message is received. Otherwise, process the task
        # definition and pass on the result.
        if current_task == b'0':
            logging.info('Waiting for work')
            poller.poll()
        else:
            logging.info('Running task')
            result_message = protocol.process_task_message(current_task)
            sink.send(result_message)

    # Exited by shutdown signal. Close all connections. This block will not
    # terminate until all results are delivered or linger has expired.
    tasks.close()
    shutdown.close()
    sink.close()
    context.destroy()
    logging.info('Done')


if __name__ == '__main__':
    worker()
