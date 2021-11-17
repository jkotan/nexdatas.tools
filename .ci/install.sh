#!/usr/bin/env bash

# workaround for incomatibility of default ubuntu 16.04 and tango configuration
if [ "$1" = "ubuntu16.04" ]; then
    docker exec --user root ndts sed -i "s/\[mysqld\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION/g" /etc/mysql/mysql.conf.d/mysqld.cnf
fi
if [ "$1" = "ubuntu20.04" ]; then
    docker exec --user root ndts sed -i "s/\[mysql\]/\[mysqld\]\nsql_mode = NO_ZERO_IN_DATE,NO_ENGINE_SUBSTITUTION\ncharacter_set_server=latin1\ncollation_server=latin1_swedish_ci\n\[mysql\]/g" /etc/mysql/mysql.conf.d/mysql.cnf
fi

# workaround for a bug in debian9, i.e. starting mysql hangs
if [ "$1" = "debian11" ]; then
    docker exec --user root ndts service mariadb restart
else
    docker exec --user root ndts service mysql stop
    if [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "ubuntu21.04" ]; then
	# docker exec --user root ndts /bin/bash -c 'mkdir -p /var/lib/mysql'
	# docker exec --user root ndts /bin/bash -c 'chown mysql:mysql /var/lib/mysql'
	docker exec --user root ndts /bin/bash -c 'usermod -d /var/lib/mysql/ mysql'
    fi
    docker exec  --user root ndts /bin/bash -c '$(service mysql start &) && sleep 30'
fi

docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get -qq update; apt-get -qq install -y   tango-db tango-common; sleep 10'
if [ "$?" != "0" ]; then exit 255; fi

echo "install tango servers"
docker exec --user root ndts /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  tango-starter tango-test'
if [ "$?" != "0" ]; then exit 255; fi

docker exec --user root ndts service tango-db restart
docker exec --user root ndts service tango-starter restart


echo "install nxsconfigserver"
docker exec --user root ndts /bin/sh -c 'export DEBIAN_FRONTEND=noninteractive;  apt-get -qq update; apt-get -qq install -y  nxsconfigserver-db; sleep 10'
if [ "$?" != "0" ]; then exit 255; fi


if [ "$2" = "2" ]; then
    echo "install python-pytango ..."
    docker exec --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y  python-pytango python-nxswriter nxswriter python-nxsconfigserver nxsconfigserver'
else
    echo "install python3-pytango ..."
    if [ "$1" = "debian10" ] || [ "$1" = "ubuntu20.04" ] || [ "$1" = "ubuntu20.10" ] || [ "$1" = "debian11" ] ; then
	docker exec --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y   python3-tango python3-nxswriter nxswriter python3-nxsconfigserver nxsconfigserver'
    else
	docker exec --user root ndts /bin/sh -c 'apt-get -qq update; export DEBIAN_FRONTEND=noninteractive; apt-get -qq install -y   python3-pytango python3-nxswriter nxswriter3 python3-nxsconfigserver nxsconfigserver3'
    fi
fi
if [ "$?" != "0" ]; then exit 255; fi


if [ "$2" = "2" ]; then
    echo "install python-nxstools"
    docker exec --user root ndts chown -R tango:tango .
    docker exec --user root ndts python setup.py -q install
else
    echo "install python3-nxstools"
    docker exec --user root ndts chown -R tango:tango .
    docker exec --user root ndts python3 setup.py -q install
fi
if [ "$?" != "0" ]; then exit 255; fi
