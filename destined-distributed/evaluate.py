# -*- coding: utf-8 -*-

import functools
import random

from destined.distribution import evaluate_distribution
from destined.generators import lookup


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


def system_random_seeds(samples):
    sysrandom = random.SystemRandom()
    for _ in range(samples):
        yield sysrandom.getrandbits(64)


def generate_with_system_seeds(specification, samples):
    ''' Generator function yielding :samples outputs of the specification
    using system random seeds. '''
    sysrandom = random.SystemRandom()
    sample_function = get_sample_function(specification)
    for _ in range(samples):
        seed = sysrandom.getrandbits(64)
        yield sample_function(seed)
