''' Manage nodes, publish tasks to workers, listen for user requests
and commands. '''

from datetime import datetime, timedelta
import logging

import msgpack
import zmq

logging.basicConfig(level=logging.INFO)
interact_address = 'tcp://*:6000'
node_address = 'tcp://*:6001'
tasks_address = 'tcp://*:6002'
publish_ms = 1000

context = zmq.Context()

interact = context.socket(zmq.ROUTER)
interact.bind(interact_address)
node = context.socket(zmq.ROUTER)
node.bind(node_address)
tasks = context.socket(zmq.PUB)
tasks.bind(tasks_address)

poller = zmq.Poller()
poller.register(interact, zmq.POLLIN)
poller.register(node, zmq.POLLIN)

tracked_nodes = {}
node_heartbeats = {}
last_publish = datetime.now()
task_def_message = msgpack.packb([1, 2, 3], use_bin_type=True)

while True:

    socks = dict(poller.poll(timeout=publish_ms))
    now = datetime.now()
    tracked_nodes = {
        ident: state
        for ident, state in tracked_nodes.items()
        if (now - node_heartbeats[ident]) < timedelta(seconds=3)
    }

    if interact in socks:
        ident, mid, request = interact.recv_multipart()
        assert mid == b''
        request = msgpack.unpackb(request, raw=False)
        if request['command'] == 'state':
            logging.info('Received :state request.')
            current_state = {'nodes': tracked_nodes}
            response = msgpack.packb(current_state, use_bin_type=True)
        elif request['command'] == 'shutdown':
            node_ident = request['node']
            if node_ident in tracked_nodes:
                logging.info(f'Received shutdown request for node {node_ident}.')
                node.send_multipart([node_ident, b'', b'shutdown'])
                response = b'ok'
            else:
                logging.info(f'Received shutdown request for unknown node {node_ident}.')
                response = b'unknown node'
        else:
            logging.warn('Received bad command.')
            response = b'bad request'
        interact.send_multipart([ident, b'', response])

    if node in socks:
        ident, mid, message = node.recv_multipart()
        assert mid == b''
        tracked_nodes[ident] = msgpack.unpackb(message, raw=False)
        node_heartbeats[ident] = now
        logging.info(f'Received heartbeat from {ident}')

    if (now - last_publish) > timedelta(milliseconds=publish_ms):
        tasks.send(task_def_message)
        last_publish = now
        logging.info('Sent task definition')
