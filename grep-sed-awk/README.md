
# Interesting Regex Related Operations

## PyPI versions

Update any outdated python packages:

    pip list --outdated --format=freeze | sed -E "s|==[0-9\.]*||" | xargs pip install --upgrade

Get only the top-level packages from `pipdeptree` output and update them:

    pipdeptree | sed -n -E "s|^([a-zA-Z0-9-]*)==[0-9\.]*|\1|p" | xargs pip install --upgrade
