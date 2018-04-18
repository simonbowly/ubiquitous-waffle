import random
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://*:5600')

time.sleep(1)

while True:
    task_def = random.choice('qwertyuiopasdfghjklzxcvbnm')
    print(f'Updating Task: {task_def}')
    socket.send(f'task_{task_def}'.encode())
    time.sleep(5)
