''' Receive results from workers and do something with them. '''

from datetime import datetime
import json
import uuid

import msgpack
import zmq


result_files = {}


def store_data(specification, results):
    key = specification['instances']['generator']
    if key not in result_files:
        base = 'data/' + str(uuid.uuid4())
        with open(base + '.spec', 'w') as outfile:
            json.dump(specification, outfile)
        result_files[key] = base + '.res'
    result_file = result_files[key]
    with open(result_file, 'a') as outfile:
        for entry in results:
            outfile.write(json.dumps(entry) + '\n')
    print(f'{len(results)} records stored at {datetime.now()}')


context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind('tcp://*:5601')


while True:
    message = socket.recv()
    decoded = msgpack.unpackb(message, raw=False)
    store_data(decoded['specification'], decoded['results'])
