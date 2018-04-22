
import logging
import random
import time

import click
import msgpack
import zmq


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


def process_task_message(message):
    task_defs = msgpack.unpackb(message, raw=False)
    task_def = random.choice(task_defs)
    logging.info(f'Running task: {task_def}')
    result = random.uniform(2, 5)
    time.sleep(result)
    return msgpack.packb(result, use_bin_type=True)


@click.command()
@click.option('--tasks-address', default='tcp://localhost:6002')
@click.option('--shutdown-address', default='tcp://localhost:6003')
@click.option('--log-file', default=None)
def worker(tasks_address, shutdown_address, log_file):

    if log_file:
        logging.basicConfig(filename=log_file, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    sink_address = 'tcp://localhost:6010'

    context = zmq.Context()

    tasks = context.socket(zmq.SUB)
    tasks.setsockopt(zmq.SUBSCRIBE, b'')
    tasks.connect(tasks_address)
    shutdown = context.socket(zmq.SUB)
    shutdown.setsockopt(zmq.SUBSCRIBE, b'')
    shutdown.connect(shutdown_address)
    sink = context.socket(zmq.PUSH)
    sink.connect(sink_address)

    current_task = b'0'

    while True:

        if shutdown.poll(timeout=0):
            logging.info('Shutting down')
            break

        current_task = get_latest_waiting(tasks, default=current_task)

        if current_task == b'0':
            logging.info('Waiting for work')
            tasks.poll()
        else:
            result_message = process_task_message(current_task)
            sink.send(result_message)


if __name__ == '__main__':
    worker()
