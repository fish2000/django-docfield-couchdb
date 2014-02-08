#!/bin/sh

export DJANGO_SETTINGS_MODULE="docfield.settings"

if [ ! -x `which couchdb` ]; then
    echo "FATAL: could not find couchdb!"
    echo "Install couchdb before running tests"
    exit 1
fi

curl -s -X PUT localhost:5984/test_docfield > /dev/null \
    && echo "+ Couch already running on port 5984" \
    || (echo "+ Launching CouchDB instance ..." && couchdb -n -b -p ./couchdb.pid)

echo "+ Running Python tests ..."
/usr/bin/env python docfield/run.py || \
    (echo "FATAL: Python tests exited with non-zero" && \
        exit 1)

COUCH_PID="./couchdb.pid"

if [ -r $COUCH_PID ]; then
    COUCH=`cat $COUCH_PID`
    echo "+ Killing couch instance: ${COUCH}"
    kill -9 $COUCH

    echo "+ Cleaning up ..."
    rm -f couchdb.pid
    rm -f couchdb.stderr
    rm -f couchdb.stdout
fi

echo "+ Done."
