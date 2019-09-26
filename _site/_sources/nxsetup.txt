=======
nxsetup
=======

Description
-----------

The nxsetup is is a command-line setup tool for NeXus servers.  It allows to set NXSDataWriter, NXSConfigServer and NXSRecSelector in Tango environment, restart them or change property names.



Synopsis
--------

.. code:: bash

	  nxsetup -x [-b <beamline>] [-m <masterHost>] [-u <local_user>] [-d <dbname>] [-j <jsonsettings>] [<server_class1> <server_class2> ... ]

	  nxsetup -r [-l level] [<server_class1> <server_class2> ... ]

	  nxsetup -s [-l level] [<server_class1> <server_class2> ... ]

	  nxsetup -a [<server_class1> <server_class2> ... ]

	  nxsetup -p -n newname -o oldname [<server_class1> <server_class2> ... ]


Options:
  -h, --help            show this help message and exit
  -b BEAMLINE, --beamline=BEAMLINE
                        name of the beamline ( default: 'nxs' )
  -m MASTERHOST, --masterHost=MASTERHOST
                        the host that stores the Mg ( default: <localhost> )
  -u USER, --user=USER  the local user
  -d DBNAME, --database=DBNAME
                        the database name ( default: 'tango' )
  -j CSJSON, --csjson=CSJSON
                        JSONSettings for the configuration server.
                        ( default: '{"host": "localhost","db": <DBNAME>,
                        "use_unicode": true', "read_default_file":
                        <MY_CNF_FILE>}'  where <MY_CNF_FILE> stays for
                        "/home/<USER>/.my.cnf" or
                        "/var/lib/nxsconfigserver/.my.cnf" )
  -x, --execute         setup servers action
  -o OLDNAME, --oldname=OLDNAME
                        old property name
  -n NEWNAME, --newname=NEWNAME
                        new property name
  -r, --restart         restart server(s) action
  -s, --start           start server(s) action
  -l LEVEL, --level=LEVEL
                        startup level
  -a RECPATH, --add-recorder-path=RECPATH
                        add recorder path
  -p, --move-prop       change property name


Example
-------

.. code:: bash

	  nxsetup -x

	  nxsetup -x -b p09 -m haso228 -u p09user -d nxsconfig  NXSConfigServer

	  nxsetup -a /usr/share/pyshared/sardananxsrecorder

	  nxsetup -p -n DefaultPreselectedComponents -o DefaultAutomaticComponents NXSRecSelector

	  nxsetup -s Pool/haso228 -l2

          nxsetup -r MacroServer -l3
