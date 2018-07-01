#!/home/simon/.virtualenvs/py36/bin/python

import datetime
import json
import operator
import os
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

sink = context.socket(zmq.PULL)
sink.bind('tcp://*:6010')
recv_count = 0
lines_written = 0
output_file = None #'/tmp/destined.out'
output_buffer = []

controller_address = 'tcp://192.168.1.106:6000'
last_poll = datetime.datetime.fromtimestamp(0)
period_seconds = 1

if output_file:
    mode = f'-> {output_file}'
else:
    mode = '(discarding results)'

while True:

    waiting = sink.poll(timeout=period_seconds)
    if waiting:
        message = sink.recv()
        result = protocol.decode(message)
        output_buffer.append(json.dumps(result))
        recv_count += 1

    now = datetime.datetime.now()
    if (now - last_poll) >= datetime.timedelta(seconds=period_seconds):
        last_poll = now

        if output_file:
            with open(output_file, 'a') as outfile:
                outfile.writelines(output_buffer)
            lines_written += len(output_buffer)
            assert lines_written == recv_count
        output_buffer = []

        socket = context.socket(zmq.REQ)
        socket.connect(controller_address)
        socket.send(protocol.msg_request_state())
        response = socket.recv()

        controller_state = protocol.decode(response)
        nodes = sorted(controller_state['nodes'].values(), key=operator.itemgetter('name'))

        os.system('clear')
        print(f'========== {now.strftime("%Y-%m-%d %H:%M:%S")} ==========')
        print(f'\nReceived messages: {recv_count} {mode}')

        for node in nodes:
            print(template.format(
                workers_all=len(node['workers']),
                workers_up=sum(worker['up'] for worker in node['workers']),
                workers_down=sum(not worker['up'] for worker in node['workers']),
                **node))
