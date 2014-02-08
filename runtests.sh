#!/bin/sh

echo "+ Launching CouchDB instance ..."
couchdb -n -b -p ./couchdb.pid

echo "+ Running Python tests ..."
/usr/bin/env python docfield/testrunner.py

COUCH=`cat ./couchdb.pid`
echo "+ Killing couch instance: ${COUCH}"
kill -9 $COUCH
#killall beam.smp

echo "+ Cleaning up ..."
rm -f couchdb.pid
rm -f couchdb.stderr
rm -f couchdb.stdout

echo "+ Done."