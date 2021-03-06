''' Manage nodes, publish tasks to workers, listen for user requests. '''

from datetime import datetime, timedelta
import json
import logging

import click
import zmq

import protocol


@click.command()
@click.argument('tasks-file', type=click.File('r'))
@click.option(
    '--client-port', type=int, default=6000,
    help='Accept client requests for state information and commands.')
@click.option(
    '--node-port', type=int, default=6001,
    help='Receive node heartbeats and send control commands.')
@click.option(
    '--worker-port', type=int, default=6002,
    help='Publish task list for workers.')
@click.option('--debug/--no-debug', default=False)
def controller(tasks_file, client_port, node_port, worker_port, debug):
    ''' Launch a controller process which publishes task definitions, keeps
    track of node states and allows clients to connect to request state and
    send commands. '''

    # Static configuration.
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    client_address = f'tcp://*:{client_port}'
    node_address = f'tcp://*:{node_port}'
    worker_address = f'tcp://*:{worker_port}'
    publish_ms = 1000

    context = zmq.Context()
    # Client connections are one off REQ-ROUTER.
    client = context.socket(zmq.ROUTER)
    client.bind(client_address)
    # Node connections are DEALER-ROUTER. Recieve node heartbeats to track
    # operating nodes. Send on shutdown commands when requested by client.
    node = context.socket(zmq.ROUTER)
    node.bind(node_address)
    # Worker connections are PUB-SUB. Interaction with workers is one-way.
    worker = context.socket(zmq.PUB)
    worker.bind(worker_address)
    # Poll only the listening ports.
    poller = zmq.Poller()
    poller.register(client, zmq.POLLIN)
    poller.register(node, zmq.POLLIN)

    # Keep node states as published by connection id.
    tracked_nodes = {}
    # Keep time of last heartbeat by connection id.
    node_heartbeats = {}
    # Last time the task list was published.
    last_publish = datetime.now()
    # Current task list being sent out.
    task_def_message = protocol.encode(json.load(tasks_file))

    logging.info(f'Accepting client connections on {client_address}')
    logging.info(f'Registering nodes on {node_address}')
    logging.info(f'Publishing tasks on {worker_address}')

    while True:
        # Wait for incoming client or node messages. Timeout functions as the
        # task publishing frequency. This should be the only blocking I/O in
        # the loop.
        socks = dict(poller.poll(timeout=publish_ms))
        now = datetime.now()
        # Discard any node states that haven't been heard from in a while.
        new_tracked_nodes = {
            ident: state
            for ident, state in tracked_nodes.items()
            if (now - node_heartbeats[ident]) < timedelta(seconds=3)
        }
        lost_nodes = [
            tracked_nodes[ident]['name']
            for ident in set(tracked_nodes) - set(new_tracked_nodes)]
        if lost_nodes:
            logging.info('Dropped nodes: ' + str(lost_nodes))
        tracked_nodes = new_tracked_nodes
        # Respond immediately if there was a client request.
        if client in socks:
            ident, mid, request = client.recv_multipart()
            assert mid == b''
            try:
                command, request = protocol.decode_client_request(request)
                if command == 'state':
                    logging.debug('Responding to state request.')
                    response = protocol.msg_controller_state(tracked_nodes)
                elif command == 'shutdown':
                    node_ident = request['node']
                    if node_ident in tracked_nodes:
                        node_name = tracked_nodes[node_ident]['name']
                        logging.info(f'Sending shutdown request to node {node_name}.')
                        node.send_multipart([node_ident, b'', protocol.MSG_NODE_SHUTDOWN])
                        response = protocol.MSG_OK
                    else:
                        logging.warn(f'Received shutdown request for unknown node {node_ident}.')
                        response = protocol.MSG_UNKNOWN_NODE
            except ValueError as e:
                logging.warn(str(e))
                response = protocol.MSG_BAD_COMMAND
            client.send_multipart([ident, b'', response])
        # Update node tracking if there was a heartbeat.
        if node in socks:
            ident, mid, message = node.recv_multipart()
            assert mid == b''
            try:
                is_new = ident not in tracked_nodes
                tracked_nodes[ident] = protocol.decode_node_heartbeat(message)
                node_heartbeats[ident] = now
                node_name = tracked_nodes[ident]['name']
                if is_new:
                    logging.info(f'Registered new node: {node_name}')
                else:
                    logging.debug(f'Received heartbeat from {node_name}')
            except ValueError as e:
                logging.warning(str(e))
        # Re-publish the task definition if period has expired.
        if (now - last_publish) > timedelta(milliseconds=publish_ms):
            worker.send(task_def_message)
            last_publish = now
            logging.debug(f'Sent task definition on {worker_address}')


if __name__ == '__main__':
    controller()
