
import time

import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect('tcp://localhost:5555')
socket.setsockopt(zmq.SUBSCRIBE, b'')

poller = zmq.Poller()                 
poller.register(socket, zmq.POLLIN)   


def check_latest():
    ''' Returns None if there is no immediately waiting message. Otherwise
    fast forwards through the message queue and returns the most recent. '''
    message = None
    while socket in dict(poller.poll(timeout=0)):
        message = socket.recv()
    return None if message is None else message.decode()

# Use case: socket does some cpu work specified by the latest
# message from the publisher.

state_message = None

while True:
    state_message = check_latest() or state_message
    print(f'Doing work for task "{state_message}"')
    time.sleep(1)

# Creating a full worker model from this:
#
# 'work' socket operates like the above. when the worker is up,
# continue doing whatever the most recent published task list
# says (i.e. choose a task by weighted priority). This should be
# 
# 'up' socket could be a ventilator. Any down workers will be
# listening, so if we want an extra worker online, a single PUSH
# starts exactly one worker (or we get an undelivered message).

# Using REQ-ROUTER
# Running workers post a REQ to one port, sleeping idle post
# a REQ to another port. Admin machine needs to stay up in this
# pattern. If it goes down, perhaps it can publish a restart
# signal to all the supervisors which just kill off their workers
# and start again...
# These ROUTERS track socket IDs of workers in each state, so they
# know to what extent they can throttle up or down. Send a REP to
# change state, if state has changed we'll get a REQ on the other
# socket (although the ID is different?).
# Perhaps also ID them to a machine in their REQ messages?
# Problem here is if you hit a busy worker it might not respond.
#
# Better alternative:
# publish "I'd like a new worker"
# if an idle worker hears this, it sends "I'd like to start" to
# the router. router replies "start" or "as you were" depending
# on whether it is still wanted (another worker might have come
# in first). This way we get first available.
# running workers can check the same for "i'd like someone to go offline"
# If we don't hear anything then escalate to the worker supervisors?

# so we have:
# a PUB-SUB model for suggesting work to do
# a PUB-SUB model for asking for changes to worker states
# a REQ-ROUTER model for workers to offer to be involved in a
# state change and the system to assign who does what

# for all PUB channels, only the latest message is relevant
# REQ sockets won't be left in a waiting state, since the router
# doesn't do anything other than route

# Calculating the system load!!
# publish an "id like a new worker" message
# all connected idle workers will report in. they could issue
# their cpu id too
# separate channel (or same?) to supervisors asking how many worker
# processes they are running. all supervisors and all idle workers
# are guaranteed to report in, so we get a picture of system state.


# For long running worker tasks, pass this function to it, to
# be checked. Should be wrapped in an object so that when the
# long running function returns, someone else can recognise that
# this worker needs to go idle.

def should_stop_work():
    sub_message = check_latest()
    if sub_message == b'reduce load':
        req_socket.send(b'offer shutdown')
        return req_socket.recv() == b'yes please':
    return False
