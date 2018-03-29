
import asyncio
import functools

from aiohttp import web
import msgpack
import zmq
import zmq.asyncio


# The ONLY thing that should be shared across coroutines!
context = zmq.asyncio.Context()
packb = functools.partial(msgpack.packb, use_bin_type=True)
unpackb = functools.partial(msgpack.unpackb, raw=False)


async def handle(request):
    ''' Coroutine serving web requests. Creates a new ZMQ client each time
    when it needs to communicate with the backend controller. Since this
    coroutine is instantiated for every request (and we may have multiple
    routes) the proper pattern should be REQ-ROUTER. '''
    socket = context.socket(zmq.REQ)
    socket.connect('inproc://req-http')
    command = request.match_info.get('command')
    message = command.encode()
    await socket.send(message)
    reply = await socket.recv()
    response = unpackb(reply)
    socket.close()
    return web.Response(text='RESPONSE: {response}  STATUS: {status}'.format(**response))


# To be responsive, backend_controller should never wait on anything
# external. It recevies requests from workers and responds immediately;
# it receives requests from the http route handler and responds immediately.
# The only awaits here are non-blocking zmq sends (?) and the blocking
# poll() which waits for input.
# Http route handler can therefore rely on this process responding immedately
# over inproc (both are always up together).

async def backend_controller():
    ''' Continuous monitoring task that listens internally on inproc for
    messages via web request, and supervises workers/systems externally
    over tcp. '''
    router_http = context.socket(zmq.ROUTER)
    router_worker = context.socket(zmq.ROUTER)
    pub_worker = context.socket(zmq.PUB)

    router_http.bind('inproc://req-http')  # REQ str().encode()  ROUTER packb(dict())
    router_worker.bind('tcp://*:5557')     # REQ str().encode()  REQ str().encode()
    pub_worker.bind('tcp://*:5555')        # PUB str().encode()

    # State information.
    workers_up = 0
    target_workers = 0

    # Main loop listens for input from the ROUTER sockets.
    poller = zmq.asyncio.Poller()
    poller.register(router_http, zmq.POLLIN)
    poller.register(router_worker, zmq.POLLIN)

    try:
        while True:
            socks = dict(await poller.poll())
            # Web server received a request we have to act on.
            if router_http in socks:
                # Update state variables and send response.
                client, mid, message = await router_http.recv_multipart()
                assert mid == b''
                if message == b'state':
                    response = 'ok'
                elif message == b'add_worker':
                    target_workers += 1
                    response = 'ok'
                elif message == b'drop_worker':
                    target_workers = max(0, target_workers - 1)
                    response = 'ok'
                else:
                    response = 'bad_request'
                reply = {
                    'response': response,
                    'status': f'UP: {workers_up:d} TARGET: {target_workers:d}'}
                await router_http.send_multipart([client, b'', packb(reply)])
                # Broadcast to workers if we need to change system state.
                if workers_up < target_workers:
                    pub_worker.send(b'worker_up')
                elif workers_up > target_workers:
                    pub_worker.send(b'worker_down')
            # Worker offered to change state. Compare to current system state
            # and return a confirmation. Trust the worker to follow through.
            if router_worker in socks:
                client, mid, message = await router_worker.recv_multipart()
                assert mid == b''
                if message == b'offer_start':
                    if workers_up < target_workers:
                        await router_worker.send_multipart([client, b'', b'start'])
                        workers_up += 1
                    else:
                        await router_worker.send_multipart([client, b'', b'do_nothing'])
                elif message == b'offer_stop':
                    if workers_up > target_workers:
                        await router_worker.send_multipart([client, b'', b'stop'])
                        workers_up -= 1
                    else:
                        await router_worker.send_multipart([client, b'', b'do_nothing'])
                else:
                    await router_worker.send_multipart([client, b'', b'bad_message'])
    except Exception as e:
        # This should be inside the while loop, sending 'internal error' back to whatever
        # socket is currently requesting if something breaks?
        print(type(e), e)
    finally:
        router_http.close()
        router_worker.close()
        pub_worker.close()


async def start_background_tasks(app):
    # If backend_controller() fails, it fails silently... and then
    # doesn't respond to the http request handler. So... make sure
    # it doesn't fail.
    app['controller'] = app.loop.create_task(backend_controller())


async def cleanup_background_tasks(app):
    # backend_controlled() should try...except asyncio.CancelledError
    # to exit gracefully when this occurs.
    app['controller'].cancel()
    await app['controller']


app = web.Application()
app.on_startup.append(start_background_tasks)
app.on_cleanup.append(cleanup_background_tasks)
app.add_routes([web.get('/{command}', handle)])
web.run_app(app)
context.destroy()


# 0MQ questions
# Can a ROUTER be a REP socket if there are multiple clients but we always reply immediately?
