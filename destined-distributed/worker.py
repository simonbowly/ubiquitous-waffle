
import random
import time
import sys

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
    print(f'Running task: {task_def}')
    time.sleep(1)
    result = random.randint(0, 1000)
    return msgpack.packb({'task': task_def, 'result': result})


@click.command()
@click.option('--sub-work-address', default='localhost:5600')
@click.option('--push-result-address', default='localhost:5601')
@click.option('--control-address', default='localhost:5602')
def worker(sub_work_address, push_result_address, control_address):

    sub_work_address = f'tcp://{sub_work_address}'
    push_result_address = f'tcp://{push_result_address}'
    control_address = f'tcp://{control_address}'

    # sub_work: receive task definitions
    # push_result: send results
    # control: send state and receive control messages
    context = zmq.Context()
    sub_work = context.socket(zmq.SUB)
    sub_work.setsockopt(zmq.SUBSCRIBE, b'')
    sub_work.connect(sub_work_address)
    push_result = context.socket(zmq.PUSH)
    push_result.connect(push_result_address)
    push_result.setsockopt(zmq.LINGER, 0)
    control = context.socket(zmq.SUB)
    control.setsockopt(zmq.SUBSCRIBE, b'')
    control.connect(control_address)

    current_message = None

    while True:
        # Check for tasks.
        current_message = get_latest_waiting(sub_work, default=current_message)
        # Check for control messages.
        control_message = get_latest_waiting(control)
        if control_message:
            print('control:', control_message)
            if control_message == b'shutdown':
                break
        # Do the work.
        if current_message is None:
            print('no work to do')
            # Use this as a sleep command which will
            # break if a control message is received.
            control.poll(timeout=1000)
        else:
            result = run_task(current_message)
            push_result.send(result)

if __name__ == '__main__':
    worker()