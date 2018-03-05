#!/bin/bash
logfile=/tmp/jekylld-build.log
pidfile=/tmp/jekylld-serve.pid
builddir=/srv/jekylld/build
repodir=/srv/git/jekylld.git
port=4001

# Kill off the old process if its pid has been recorded.
if [ -f $pidfile ]; then
    kill -9 $(cat $pidfile)
    rm -f $pidfile
fi

# Checkout a fresh clone.
rm -rf $builddir
mkdir -p $builddir
git clone $repodir $builddir

# Start the jekyll server and store its pid.
cd $builddir
bundle exec jekyll serve --detach --no-watch --port $port > $logfile
sed -E -n "s|.*detached with pid '([0-9]+)'.*|\1|p" $logfile > $pidfile

exit 0
