#!/usr/bin/env python

import os
import sys

import click

@click.command()
@click.argument('central_ip', type=str)
@click.argument('nworkers', type=int)
@click.option('--post-shutdown/--no-post-shutdown', default=False)
def install(central_ip, nworkers, post_shutdown):
    with open('template.service') as infile:
        template = infile.read()
    contents = template.format(
        python_bin=sys.executable,
        install_dir=os.path.dirname(os.path.abspath(__file__)),
        central_ip=central_ip,
        nworkers=nworkers,
        post_shutdown=('' if post_shutdown else 'no-'))
    sys.stdout.write(contents)


install()
