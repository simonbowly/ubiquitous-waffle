''' Query system state, send control signals. '''

from pprint import pprint
import time

import zmq

import protocol


template = '''
Node:       {name}
State:      {state}
Workers:    {workers_all} ({workers_up} up, {workers_down} down)
CPU Util:   {cpu_percent:>5.1f} %
Mem Util:   {mem_percent:>5.1f} %
'''


context = zmq.Context()

controller_address = 'tcp://localhost:6000'

socket = context.socket(zmq.REQ)
socket.connect(controller_address)
socket.send(protocol.msg_request_state())
response = socket.recv()

controller_state = protocol.decode(response)

for node in controller_state['nodes'].values():
    print(template.format(
        workers_all=len(node['workers']),
        workers_up=sum(worker['up'] for worker in node['workers']),
        workers_down=sum(not worker['up'] for worker in node['workers']),
        **node))
