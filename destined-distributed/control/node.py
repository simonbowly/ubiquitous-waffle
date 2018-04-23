
import contextlib
from datetime import datetime, timedelta
import logging
import subprocess

import click
import zmq

import protocol


@click.command()
@click.argument('node-name')
@click.argument('nworkers', type=int)
@click.option(
    '--controller-address', default='localhost:6001',
    help='Send heartbeats to controller and receive shutdown commands.')
@click.option(
    '--worker-port', type=int, default=6003,
    help='Publish shutdown signal to workers on localhost.')
@click.option(
    '--tasks-address', default='localhost:6002',
    help='Configure workers: subscribe for task definitions.')
@click.option(
    '--sink-address', default='localhost:6010',
    help='Configure workers: push results.')
def node(node_name, nworkers, controller_address, worker_port,
         tasks_address, sink_address):
    ''' Launch a node controlling :nworkers worker processes. The node sends
    status heartbeats to the controller and listens for a shutdown message. '''

    logging.basicConfig(level=logging.INFO)
    heartbeat_ms = 1000

    context = zmq.Context()
    # DEALER-ROUTER for sending status and receiving commands.
    controller = context.socket(zmq.DEALER)
    controller.connect(f'tcp://{controller_address}')
    controller.setsockopt(zmq.LINGER, 0)
    # PUB-SUB to send shutdown signal to workers.
    worker_shutdown = context.socket(zmq.PUB)
    worker_shutdown.bind(f'tcp://*:{worker_port}')

    # Launch the managed worker processes.
    workers = []
    for worker_id in range(nworkers):
        command = [
            'python', 'worker.py',
            f'--tasks-address={tasks_address}',
            f'--sink-address={sink_address}',
            f'--shutdown-address=localhost:{worker_port}',
            f'--log-file=/tmp/worker{worker_id + 1}.log']
        worker = subprocess.Popen(command)
        workers.append(worker)

    last_heartbeat = datetime.now() - timedelta(milliseconds=heartbeat_ms * 2)
    state = 'running'

    logging.info(f'Running as named node "{node_name}"')
    logging.info(f'Sending heartbeats to {controller_address}')
    logging.info(f'Worker shutdown signal on port {worker_port}')
    logging.info(f'Task address set for workers {tasks_address}')
    logging.info(f'Sink address set for workers {sink_address}')
    for worker_id, worker in enumerate(workers):
        logging.info(f'Launched worker on PID {worker.pid} logging to /tmp/worker{worker_id + 1}.log')

    while True:
        # Update status for the worker processes.
        for worker in workers:
            with contextlib.suppress(subprocess.TimeoutExpired):
                worker.wait(timeout=0)
        # Send the heartbeat message (node state) if period has expired.
        now = datetime.now()
        if (now - last_heartbeat) > timedelta(milliseconds=heartbeat_ms):
            message = protocol.msg_node_state(node_name, state, workers)
            controller.send_multipart([b'', message])
            last_heartbeat = now
            logging.info(f'Sent heartbeat to {controller_address}')
        # Check to see if we get any commands back. This also functions
        # as the heartbeat sleep command (only blocking call in loop).
        waiting = controller.poll(timeout=heartbeat_ms)
        if waiting:
            mid, message = controller.recv_multipart()
            assert mid == b''
            if message == protocol.MSG_NODE_SHUTDOWN:
                logging.info(f'Signalling worker shutdown on port {worker_port}')
                state = 'shutting down'
                worker_shutdown.send(b'0')
            else:
                logging.warning(f'Received unknown command: {message}')
        # Can exit if in shutdown state and all workers are closed.
        if state == 'shutting down':
            if all(worker.returncode is not None for worker in workers):
                logging.info('All workers down')
                break
            # TODO sigterm/sigkill after a certain amount of time.


if __name__ == '__main__':
    node()
