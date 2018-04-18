
import signal
import subprocess

import click
import zmq


@click.command()
@click.argument('nworkers', type=int)
@click.option('--sub-work-address', default=None)
@click.option('--push-result-address', default=None)
@click.option('--control-port', default=5602)
def supervisor(nworkers, sub_work_address, push_result_address, control_port):

    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f'tcp://*:{control_port}')

    base_command = ['python', 'worker.py']
    if sub_work_address:
        base_command.append(f'--sub-work-address={sub_work_address}')
    if push_result_address:
        base_command.append(f'--push-result-address={push_result_address}')
    base_command.append(f'--control-address=localhost:{control_port}')

    workers = []
    for i in range(nworkers):
        command = base_command + [f'--log-file=worker{i+1}.log']
        worker = subprocess.Popen(command, start_new_session=True)
        workers.append(worker)
        click.echo(f'Worker {i+1} PID {worker.pid}')

    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    click.echo("Shutting down workers.")

    socket.send(b'shutdown')

    for worker in workers:
        try:
            worker.wait(timeout=10)
        except subprocess.TimeoutExpired:
            worker.send_signal(signal.SIGINT)
        worker.wait()
        click.echo(f'Worker on {worker.pid} exited with return code {worker.returncode}.')


if __name__ == '__main__':
    supervisor()
