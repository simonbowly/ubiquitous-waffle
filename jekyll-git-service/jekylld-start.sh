#!/bin/bash
repodir=/srv/git/jekylld.git

jekylld-restart-serve.sh

(inotifywait -m -e moved_to $repodir/refs/heads/ & echo $! >&3) 3>/tmp/jekylld-watch.pid |
    while read line; do
        echo "jekylld: restarting"
        jekylld-restart-serve.sh
    done &

exit 0
