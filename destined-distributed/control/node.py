
import contextlib
from datetime import datetime, timedelta
import logging
import subprocess

import msgpack
import psutil
import zmq

logging.basicConfig(level=logging.INFO)
controller_address = 'tcp://localhost:6001'
shutdown_port = 6003
heartbeat_ms = 1000
worker_ids = [1, 2]
name = 'derby02'

worker_address = f'tcp://*:{shutdown_port}'

context = zmq.Context()

controller = context.socket(zmq.DEALER)
controller.connect(controller_address)
worker_shutdown = context.socket(zmq.PUB)
worker_shutdown.bind(worker_address)

last_heartbeat = datetime.now() - timedelta(milliseconds=heartbeat_ms * 2)
state = 'running'

workers = []
for worker_id in worker_ids:
    command = [
        'python', 'worker.py',
        f'--shutdown-address=tcp://localhost:{shutdown_port}',
        f'--log-file=worker{worker_id}.log']
    worker = subprocess.Popen(command)
    workers.append(worker)
    logging.info(f'Worker {worker_id} PID {worker.pid}')

while True:
    # Update the worker status.
    for worker in workers:
        with contextlib.suppress(subprocess.TimeoutExpired):
            worker.wait(timeout=0)
    worker_states = [
        {
            'pid': worker.pid,
            'up': worker.returncode is None,
            'returncode': worker.returncode}
        for worker in workers]
    # Send the heartbeat message (node state).
    now = datetime.now()
    if (now - last_heartbeat) > timedelta(milliseconds=heartbeat_ms):
        current_state = {
            'name': name,
            'cpu_freq': psutil.cpu_freq().current,
            'cpu_percent': psutil.cpu_percent(),
            'mem_percent': psutil.virtual_memory().percent,
            'time': datetime.now().isoformat(),
            'state': state,
            'workers': worker_states
            }
        message = msgpack.packb(current_state, use_bin_type=True)
        controller.send_multipart([b'', message])
        last_heartbeat = now
        logging.info('Sent heartbeat')
    # Check to see if we get any commands back. This also functions
    # as the heartbeat sleep command.
    waiting = controller.poll(timeout=heartbeat_ms)
    if waiting:
        mid, message = controller.recv_multipart()
        assert mid == b''
        if message == b'shutdown':
            logging.info('Received shutdown command')
            state = 'shutting down'
            worker_shutdown.send(b'0')
            # keep heartbeating as we shut down workers
        else:
            logging.warning(f'Received unknown command: {message}')
    # Can exit if in shutdown state and all workers are closed.
    if state == 'shutting down':
        if all(not w['up'] for w in worker_states):
            logging.info('All workers down')
            break
        # Might need to do a more aggressive shutdown here?
