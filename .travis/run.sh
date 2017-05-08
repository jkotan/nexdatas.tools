#!/usr/bin/env bash

echo "test python-nxstools"
docker exec -it ndts python setup.py test
if [ $? -ne "0" ]
then
    exit -1
fi
