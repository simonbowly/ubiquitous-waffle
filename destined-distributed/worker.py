
import logging
import random

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


def run_task(message):
    task_def = message.decode()
    logging.info(f'Running task: {task_def}')
    result = [sum(random.random() for _ in range(3000000)) for _ in range(3)]
    return msgpack.packb({'task': task_def, 'result': result})


@click.command()
@click.option('--sub-work-address', default='localhost:5600')
@click.option('--push-result-address', default='localhost:5601')
@click.option('--control-address', default='localhost:5602')
@click.option('--log-file', default=None)
def worker(sub_work_address, push_result_address, control_address, log_file):

    if log_file:
        logging.basicConfig(filename=log_file, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    # sub_work: receive task definitions
    # push_result: send results
    # control: send state and receive control messages
    context = zmq.Context()

    sub_work = context.socket(zmq.SUB)
    sub_work.setsockopt(zmq.SUBSCRIBE, b'')
    sub_work.connect(f'tcp://{sub_work_address}')

    push_result = context.socket(zmq.PUSH)
    push_result.setsockopt(zmq.LINGER, 0)
    push_result.connect(f'tcp://{push_result_address}')

    control = context.socket(zmq.SUB)
    control.setsockopt(zmq.SUBSCRIBE, b'')
    control.connect(f'tcp://{control_address}')

    poller = zmq.Poller()
    poller.register(sub_work, zmq.POLLIN)
    poller.register(control, zmq.POLLIN)

    # Can't do anything until at least one task or control message is received.
    current_message = b'idle'
    logging.info('Waiting for first task')
    poller.poll()

    while True:
        # Check for control messages.
        control_message = get_latest_waiting(control)
        if control_message:
            logging.info(f'control: {control_message}')
            if control_message == b'shutdown':
                break
        # Check for tasks.
        current_message = get_latest_waiting(sub_work, default=current_message)
        if current_message == b'idle':
            # Block until control or task messages received.
            logging.info('idle - no work to do')
            poller.poll()
        else:
            # Do the work.
            result = run_task(current_message)
            push_result.send(result)


if __name__ == '__main__':
    worker()
