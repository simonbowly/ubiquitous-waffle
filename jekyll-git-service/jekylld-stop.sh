#!/bin/bash

# Kill off both the server and watcher processes

pidfile=/tmp/jekylld-serve.pid
if [ -f $pidfile ]; then
    echo "Kill jekylld-serve $(cat $pidfile)"
    kill -9 $(cat $pidfile)
    rm -f $pidfile
fi

pidfile=/tmp/jekylld-watch.pid
if [ -f $pidfile ]; then
    echo "Kill jekylld-watch $(cat $pidfile)"
    kill -9 $(cat $pidfile)
    rm -f $pidfile
fi

exit 0
