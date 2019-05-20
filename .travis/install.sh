#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ $1 = "ubuntu16.04" ]; then
    docker exec -it --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi

docker exec -it --user root ndts service mysql stop
docker exec -it --user root ndts /bin/sh -c '$(service mysql start &) && sleep 30'

docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ $? -ne "0" ]
then
    exit -1
fi
echo "install tango servers"
docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test liblog4j1.2-java'
if [ $? -ne "0" ]
then
    exit -1
fi

docker exec -it --user root ndts service tango-db restart
docker exec -it --user root ndts service tango-starter restart


if [ $2 = "2" ]; then
    echo "install python-pytango ..."
    docker exec -it --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y   python-pytango python-fabio python-argcomplete'
else
    echo "install python3-pytango ..."
    docker exec -it --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y   python3-pytango python3-fabio python3-argcomplete'
fi
if [ $? -ne "0" ]
then
    exit -1
fi

if [[ $1 -ne "debian8" ]]; then
    if [ $2 = "2" ]; then
	echo "install python-whichcraft"
	docker exec -it --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y python-whichcraft'
    else
	echo "install python3-whichcraft"
	docker exec -it --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y python3-whichcraft'
    fi
fi
if [ $? -ne "0" ]
then
    exit -1
fi

echo "install sardana, taurus and nexdatas"
docker exec -it --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  nxsconfigserver-db; sleep 10; apt-get -qq install -y python-nxsconfigserver '
if [ $? -ne "0" ]
then
    exit -1
fi

if [ $2 = "2" ]; then
    echo "install python-nxstools"
    docker exec -it --user root ndts chown -R tango:tango .
    docker exec -it --user root ndts python setup.py -q install
else
    echo "install python3-nxstools"
    docker exec -it --user root ndts chown -R tango:tango .
    docker exec -it --user root ndts python3 setup.py -q install
fi
if [ $? -ne "0" ]
then
    exit -1
fi
