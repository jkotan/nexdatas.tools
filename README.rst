Welcome to nxstools's documentation!
====================================

Authors: Jan Kotanski, Eugen Wintersberger, Halil Pasic
Introduction


-------------------------
Installation from sources
-------------------------

Install the dependencies:

    PyTango

Download the latest NXS Tools version from

    https://github.com/jkotan/nexdatas.tools/

Extract sources and run

$ python setup.py install


=======
nxsdata
=======

The nxsdata program is a command-line interface to Nexus Data Tango Server.
Program allows one to store NeXuS Data in H5 files.
The writer provides storing data from other Tango devices, various databases
as well as passed by a user client via JSON strings.


Usage:

.. code:: bash

	  nxsdata <command> [-s <nexus_server>]  [<arg1> [<arg2>  ...]]

e.g.:

.. code:: bash

	  nxsdata openfile -s p02/tangodataserver/exp.01  $HOME/myfile.h5

Commands:
   openfile [-s <nexus_server>]  <file_name>
          open new H5 file
   setdata [-s <nexus_server>] <json_data_string>
          assign global JSON data
   openentry [-s <nexus_server>] <xml_config>
          create new entry
   record [-s <nexus_server>]  <json_data_string>
          record one step with step JSON data
   closeentry [-s <nexus_server>]
          close the current entry
   closefile [-s <nexus_server>]
          close the current file
   servers [-s <nexus_server/host>]
          get lists of tango data servers from the current tango host


Options:
  -h, --help            show this help message and exit
  -s SERVER, --server=SERVER
                        tango data server device name


=========
nxsconfig
=========

The nxsconfig program
is a command-line interface to NXS Configuration Tango Server.
It allows one to read XML configuration datasources
and components. It also gives possibility to
perform the process of component merging.

Usage:

.. code:: bash

	  nxsconfig <command> [-s <config_server>]  [-d] [-m] [-n] [<name1>] [<name2>] [<name3>] ...

e.g.:

.. code:: bash

	  nxsconfig list -s p02/xmlconfigserver/exp.01 -d

Commands:
   list [-s <config_server>] [-m]
          list names of available components
   list -d [-s <config_server>]
          list names of available datasources
   show [-s <config_server>] [-m] component_name1 component_name2 ...
          show components with given names
   show -d [-s <config_server>] dsource_name1 dsource_name2 ...
          show datasources with given names
   get [-s <config_server>]  [-m] component_name1 component_name2 ...
          get merged configuration of components
   sources [-s <config_server>] [-m] component_name1 component_name2 ...
          get a list of component datasources
   components [-s <config_server>] component_name1 component_name2 ...
          get a list of dependent components
   variables [-s <config_server>] [-m] component_name1 component_name2 ...
          get a list of component variables
   data [-s <config_server>] json_data
          set values of component variables
   record [-s <config_server>]  component_name1
          get a list of datasource record names from component
   record -d [-s <config_server>] datasource_name1
          get a list of datasource record names
   servers [-s <config_server/host>]
          get lists of configuration servers from the current tango host
   describe [-s <config_server>] [-m | -p] component_name1 component_name2 ...
          show all parameters of given components
   describe|info -d [-s <config_server>] dsource_name1 dsource_name2 ...
          show all parameters of given datasources
   info [-s <config_server>] [-m | -p] component_name1 component_name2 ...
          show source parameters of given components
   geometry [-s <config_server>] [-m | -p] component_name1 component_name2 ...
          show transformation parameters of given components

Options:
  -h, --help            show this help message and exit
  -s SERVER, --server=SERVER
                        configuration server device name
  -d, --datasources     perform operation on datasources
  -m, --mandatory       make use mandatory components as well
  -p, --private         make use private components, i.e. starting with '__'
  -n, --no-newlines     split result with space characters

=======
nxsetup
=======

The nxsetup is is a command-line setup tool for NeXus servers.  It allows to set NXSDataWriter, NXSConfigServer and NXSRecSelector in Tango environment, restart them or change property names.



Usage:

.. code:: bash

	  nxsetup -x [-j <jsonsettings>] [<server_class1> <server_class2> ... ]

	  nxsetup -r [<server_class1> <server_class2> ... ]

	  nxsetup -p -n newname -o oldname [<server_class1> <server_class2> ... ]


Options:
  -h, --help            show this help message and exit
  -b BEAMLINE, --beamline=BEAMLINE
                        name of the beamline
  -m MASTERHOST, --masterHost=MASTERHOST
                        the host that stores the Mg
  -u USER, --user=USER  the local user
  -d DBNAME, --database=DBNAME
                        the database name
  -j CSJSON, --csjson=CSJSON
                        JSONSettings for the configuration server
  -x, --execute         setup servers action
  -o OLDNAME, --oldname=OLDNAME
                        old property name
  -n NEWNAME, --newname=NEWNAME
                        new property name
  -r, --restart         restart server(s) action
  -a RECPATH, --add-recorder-path=RECPATH
                        add recorder path
  -p, --move-prop       change property name


=========
nxcollect
=========

The nxsconfig is  a command-line tool dedicated to collect detector images of external formats into the NeXus master file.  The images to collect should be denoted by postrun fields inside NXcollection groups.


Usage:

.. code:: bash

	   nxscollect [-x|-t] [<options>] <command> <main_nexus_file>

e.g.:

.. code:: bash

	   nxscollect -x -c1 /tmp/gpfs/raw/scan_234.nxs



Options:
  -h, --help            show this help message and exit
  -x, --execute         execute the collecting process
  -t, --test            exceute the process in test mode without changing any
                        files
  -c COMPRESSION, --compression=COMPRESSION
                        deflate compression rate from 0 to 9
  -s, --skip_missing    skip missing files
  -r, --replace_nexus_file
                        if it is set the old file is not copied into a file
                        with .__nxscollect__old__* extension



=========
nxscreate
=========

The nxscreate program allows one to create simple datasources and components.

Usage:

.. code:: bash

	  nxscreate  <command> [ <options>]  [<arg1> [<arg2>  ...]]


The following commands are available:


nxscreate clientds
------------------

It creates a set of CLIENT datasources.

Usage:

.. code:: bash

	  nxscreate clientds [options] [name1] [name2]

e.g.:

.. code:: bash

	   nxscreate clientds starttime -b
	   nxscreate clientds title -d /home/user/xmldir
	   nxscreate clientds -p exp_c -f1 -l4 -b
	   nxscreate clientds -p hasppXX:10000/expchan/vfcadc_exp/ -f1 -l8  -m -b -s exp_vfc

- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default: <directory> is '.'
           <server> is taken from Tango DB


It creates a set of client datasources.

Options:
  -h, --help            show this help message and exit
  -p DEVICE, --device-prefix=DEVICE
                        device prefix, i.e. exp_c (mandatory w/o <name1>)
  -f FIRST, --first=FIRST
                        first index (mandatory w/o <name1>)
  -l LAST, --last=LAST  last index (mandatory w/o <name1>)
  -d DIRECTORY, --directory=DIRECTORY
                        output datasource directory
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter
  -s DSOURCE, --datasource-prefix=DSOURCE
                        datasource prefix, i.e. counter
  -b, --database        store components in Configuration Server database
  -m, --minimal_device  device name without first '0'
  -r SERVER, --server=SERVER
                        configuration server device name

nxscreate tangods
-----------------

It creates a set of TANGO datasources.

Usage:

.. code:: bash

	  nxscreate tangods [options]

e.g.:

.. code:: bash

	   nxscreate tangods -f1 -l2  -p p09/motor/exp. -o exp_mot
	   nxscreate tangods -f1 -l32  -p p02/motor/eh1a. -o exp_mot -b
	   nxscreate tangods -f1 -l32  -p p01/motor/oh1. -o exp_mot -b
	   nxscreate tangods -f1 -l8  -p pXX/slt/exp. -o slt_exp_ -s hasppXX.desy.de -b

- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default: <directory> is '.'
           <server> is taken from Tango DB
           <datasource> is 'exp_mot'
           <host>, <port> are taken from <server>

Options:
  -h, --help            show this help message and exit
  -p DEVICE, --device-prefix=DEVICE
                        device prefix, i.e. exp_c (mandatory)
  -f FIRST, --first=FIRST
                        first index (mandatory)
  -l LAST, --last=LAST  last index (mandatory)
  -a ATTRIBUTE, --attribute=ATTRIBUTE
                        tango attribute name
  -o DATASOURCE, --datasource-prefix=DATASOURCE
                        datasource-prefix
  -d DIRECTORY, --directory=DIRECTORY
                        output datasource directory
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter
  -s HOST, --host=HOST  tango host name
  -t PORT, --port=PORT  tango host port
  -b, --database        store components in Configuration Server database
  -r SERVER, --server=SERVER
                        configuration server device name


nxscreate deviceds
------------------

It creates a set of TANGO datasources for all device attributes.

Usage:

.. code:: bash

	  nxscreate deviceds [options] [dv_attr1 [dv_attr2 [dv_attr3 ...]]]

e.g.:

.. code:: bash

	   nxscreate deviceds  -v p09/pilatus/haso228k
	   nxscreate deviceds  -v p09/lambda2m/haso228k  -s haslambda -b
	   nxscreate deviceds  -v p09/pilatus300k/haso228k -b -o pilatus300k_ RoI Energy ExposureTime

- without <dv_attr1>: datasources for all attributes are created
- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default: <directory> is '.'
           <server> is taken from Tango DB
           <datasource> is 'exp_mot'
           <host>, <port> are taken from <server>

Options:
  -h, --help            show this help message and exit
  -v DEVICE, --device=DEVICE
                        device, i.e. p09/pilatus300k/01 (mandatory)
  -o DATASOURCE, --datasource-prefix=DATASOURCE
                        datasource-prefix
  -d DIRECTORY, --directory=DIRECTORY
                        output datasource directory
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter
  -s HOST, --host=HOST  tango host name
  -t PORT, --port=PORT  tango host port
  -b, --database        store components in Configuration Server database
  -n, --no-group        don't create common group with a name of datasource
                        prefix
  -r SERVER, --server=SERVER
                        configuration server device name


nxscreate onlineds
------------------

It creates a set of motor datasources from an online xml file.

Usage:

.. code:: bash

	  nxscreate onlineds [options] inputFile

e.g.:

.. code:: bash

	   nxscreate onlineds -b
	   nxscreate onlineds -d /home/user/xmldir
	   nxscreate onlineds

- with -b: datasources are created in Configuration Server database
- with -d <directory>: datasources are created on the local filesystem
- without -b or -d <directory>: run in the test mode
- default: <inputFile> is '/online_dir/online.xml'
           <server> is taken from Tango DB

Options:
  -h, --help            show this help message and exit
  -b, --database        store components in Configuration Server database
  -d DIRECTORY, --directory=DIRECTORY
                        output directory where datasources will be saved
  -n, --nolower         do not change aliases into lower case
  -r SERVER, --server=SERVER
                        configuration server device name
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter


nxscreate onlinecp
------------------

It creates a detector component from the online.xml file
and its set of datasources.

Usage:

.. code:: bash

	  nxscreate onlinecp [options] inputFile

e.g.:

.. code:: bash

	  nxscreate onlinecp
	  nxscreate onlinecp -c pilatus
	  nxscreate onlinecp -c lambda -d /home/user/xmldir/

- without '-c <component>': show a list of possible components
- without '-d <dircetory>:  components are created in Configuration Server database
- with -d <directory>: components are created on the local filesystem
- default: <inputFile> is '/online_dir/online.xml'
           <server> is taken from Tango DB


Options:
  -h, --help            show this help message and exit
  -c COMPONENT, --component=COMPONENT
                        component namerelated to the device name from
                        <inputFile>
  -r SERVER, --server=SERVER
                        configuration server device name
  -n, --nolower         do not change aliases into lower case
  -o, --overwrite       overwrite existing component
  -d DIRECTORY, --directory=DIRECTORY
                        output directory where datasources will be stored. If
                        it is not set components are stored in Configuration
                        Server database
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter


nxscreate comp
--------------

It creates a set of simple components.

Usage:

.. code:: bash

	  nxscreate comp [options] [name1] [name2] ...

e.g.

.. code:: bash

	  nxscreate comp  counter 
	  nxscreate comp -f1 -l -p exp_c01 -b 
	  nxscreate comp -c lambda -d /home/user/xmldir/ 
	  nxscreate comp -n '/entry$var.serialno:NXentry/instrument/sis3302:NXdetector/collection:NXcollection/' -p sis3302_1_roi -f1 -l4  -s STEP -t NX_FLOAT64 -k -b -m 
	  nxscreate comp -n '/entry$var.serialno:NXentry/instrument/eh1_mca01:NXdetector/data' eh1_mca01 -s STEP -t NX_FLOAT64 -i -b -c SPECTRUM
	    
- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory> 
- default: <directory> is '.' 
           <server> is taken from Tango DB
           <strategy> is step
           <type> is NX_FLOAT
           <chunk> is SCALAR
           <nexuspath> is '/entry$var.serialno:NXentry/instrument/collection/



Options:
  -h, --help            show this help message and exit
  -p DEVICE, --device-prefix=DEVICE
                        device prefix, i.e. exp_c
  -f FIRST, --first=FIRST
                        first index
  -l LAST, --last=LAST  last index
  -d DIRECTORY, --directory=DIRECTORY
                        output component directory
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter
  -n NEXUSPATH, --nexuspath=NEXUSPATH
                        nexus path with field name
  -s STRATEGY, --strategy=STRATEGY
                        writing strategy, i.e. STEP, INIT, FINAL, POSTRUN
  -t TYPE, --type=TYPE  nexus type of the field
  -u UNITS, --units=UNITS
                        nexus units of the field
  -k, --links           create datasource links
  -b, --database        store components in Configuration Server database
  -r SERVER, --server=SERVER
                        configuration server device name
  -c CHUNK, --chunk=CHUNK
                        chunk format, i.e. SCALAR, SPECTRUM, IMAGE
  -m, --minimal_device  device name without first '0'
