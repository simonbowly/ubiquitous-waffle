
from unittest import mock

import msgpack

import tasks


@mock.patch(
    'tasks.get_sample_function',
    return_value=lambda seed: 'instance-data')
def test_process_task_message(get_sample_function):
    task_def = [{
        'type': 'destined',
        'spec': 'destined-spec',
        'count': 10
    }]
    message = msgpack.packb(task_def, use_bin_type=True)
    response = tasks.process_task_message(message)
    get_sample_function.assert_called_once_with('destined-spec')
    response = msgpack.unpackb(response, raw=False)
    assert response['task'] == task_def[0]
    assert response['result'] == ['instance-data'] * 10
