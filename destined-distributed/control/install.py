#!/usr/bin/env python

import os
import sys

import click

@click.command()
@click.argument('central_ip', type=str)
@click.argument('nworkers', type=int)
def install(central_ip, nworkers):
    click.echo(sys.version, err=True)
    with open('template.service') as infile:
        template = infile.read()
    contents = template.format(
        python_bin=sys.executable,
        install_dir=os.path.dirname(os.path.abspath(__file__)),
        central_ip=central_ip,
        nworkers=nworkers)
    service_file = 'destined-distribute.service'
    with open(service_file, 'w') as outfile:
        sys.stdout.write(contents)


install()
