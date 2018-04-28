
import functools
import random

import msgpack

from destined.distribution import evaluate_distribution
from destined.generators import lookup


encode = functools.partial(msgpack.packb, use_bin_type=True)
decode = functools.partial(msgpack.unpackb, raw=False)


def get_sample_function(specification):
    ''' Still working on this spec... read a random generator specification
    (see example files) including evaluation/attribute commands. Returns a
    function which, given a random seed, generates an instance and returns
    its attributes. '''

    # Generating function taking a randgen object and returning an instance.
    generate = evaluate_distribution(specification['instances'], lookup)

    # Function to evaluate features of the generated instance.
    attributes = lookup(specification['attributes'])

    # Sample function returns a data point given a seed value.
    def sample(seed):
        randgen = random.Random(seed)
        instance = generate(randgen)
        return dict(attributes(instance), seed=seed)

    return sample


def process_task_message(message):
    ''' Decode the current task definition message, carry out a task and
    return the encoded result message to be sent to the result sink. '''
    task_defs = decode(message)
    task_def = random.choice(task_defs)
    if task_def['type'] == 'destined':
        sample = get_sample_function(task_def['spec'])
        sysrandom = random.SystemRandom()
        result = [
            sample(sysrandom.getrandbits(32))
            for _ in range(task_def['count'])]
    else:
        raise ValueError()
    return encode({
        'task': task_def,
        'result': result
        })
