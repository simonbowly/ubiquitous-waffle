''' This should hold all logic defining communication patterns, while process
scripts define control logic.

Senders use these functions to formulate messages (not raw encode/decode).
Message creators should error before send if a valid message could not be built.

Receivers use these functions to decode/validate received messages.
Message decoders should raise exception if message is not valid.

e.g. for client-controller REQ-ROUTER

client_request_state()          -> encoded message
client_request_shutdown(node)   -> encoded message
decode_client_request(message)  -> checked dict, raise exception if invalid
controller_send_state(data)     -> encoded message

'''

import functools
import random
import time

import msgpack
import psutil


encode = functools.partial(msgpack.packb, use_bin_type=True)
decode = functools.partial(msgpack.unpackb, raw=False)


MSG_NODE_SHUTDOWN = b'node_shutdown'
MSG_UNKNOWN_NODE = b'unknown_node'
MSG_BAD_COMMAND = b'bad_command'
MSG_OK = b'ok'


def msg_node_state(node_name, node_state, workers):
    ''' Heartbeat message send by nodes. '''
    return encode({
        'name': node_name,
        'state': node_state,
        'workers': [
            {
                'pid': worker.pid,
                'up': worker.returncode is None,
                'returncode': worker.returncode}
            for worker in workers],
        'cpu_percent': psutil.cpu_percent(),
        'mem_percent': psutil.virtual_memory().percent
        })


def msg_request_state():
    ''' Request by client to controller for full system state. '''
    return encode({'command': 'state'})


def msg_request_shutdown(node_ident):
    ''' Request by client for controller to shutdown a node. '''
    return encode({'command': 'shutdown', 'node': node_ident})


def msg_controller_state(tracked_nodes):
    ''' Full system state from controller. :tracked_nodes is just a list
    of node state messages. '''
    return encode({'nodes': tracked_nodes})


def msg_task_def():
    return encode([1, 2, 3])


def process_task_message(message):
    ''' Decode the current task definition message, carry out a task and
    return the encoded result message to be sent to the result sink. '''
    task_defs = decode(message)
    task_def = random.choice(task_defs)
    result = random.uniform(2, 5)
    time.sleep(result)
    return encode({
        'task': task_def,
        'result': result
        })


def decode_client_request(message):
    try:
        request = decode(message)
    except ValueError as e:
        raise ValueError('Client request not decodable: ' + str(e))
    if type(request) is not dict:
        raise ValueError('Client request is not key-value')
    if 'command' not in request:
        raise ValueError('No command in client request message.')
    if request['command'] == 'state':
        return 'state', None
    if request['command'] == 'shutdown':
        if 'node' not in request:
            raise ValueError('Client shutdown request does not specify a node.')
        return 'shutdown', request
    raise ValueError('Client request sent unknown command: {command}'.format(**request))


def decode_node_heartbeat(message):
    try:
        heartbeat = decode(message)
    except ValueError as e:
        raise ValueError('Node heartbeat not decodable: ' + str(e))
    if type(heartbeat) is not dict:
        raise ValueError('Node heartbeat is not key-value')
    if 'name' not in heartbeat:
        raise ValueError('Node heartbeat does not contain name key')
    return heartbeat
