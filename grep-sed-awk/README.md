
# Interesting Regex Related Operations

## PyPI versions

Update any outdated python packages:

    pip list --outdated --format=freeze | sed -E "s|==[0-9\.]*||" | xargs pip install --upgrade

Get only the top-level packages from `pipdeptree` output and update them:

    pipdeptree | sed -n -E "s|^([a-zA-Z0-9-]*)==[0-9\.]*|\1|p" | xargs pip install --upgrade

## Finding virtual and physical cores

Python on linux:

    import re

    with open('/proc/cpuinfo') as infile:
        data = infile.read()
        physical_cores = int(re.search('cpu cores\s:\s([0-9])+', data).group(1))
        virtual_cores = int(re.search('siblings\s:\s([0-9])+', data).group(1))

Bash on linux:

    cat /proc/cpuinfo | sed -n -E "s|cpu cores\s:\s([0-9]+)|\1|p" | head -n 1
    cat /proc/cpuinfo | sed -n -E "s|siblings\s:\s([0-9]+)|\1|p" | head -n 1
