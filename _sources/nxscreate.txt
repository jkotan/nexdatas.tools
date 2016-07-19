=========
nxscreate
=========

Description
-----------

The nxscreate program allows one to create simple datasources and components.

Synopsis
--------

.. code:: bash

	  nxscreate  <command> [ <options>]  [<arg1> [<arg2>  ...]]


The following commands are available: clientds, tangods, deviceds, onlineds, onlinecp, comp.


nxscreate clientds
------------------

It creates a set of CLIENT datasources.

Synopsis
""""""""

.. code:: bash

	  nxscreate clientds [options] [name1] [name2]

- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default <directory> is '.'
- default <server> is taken from Tango DB


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

Example
"""""""

.. code:: bash

	   nxscreate clientds starttime -b
	   nxscreate clientds title -d /home/user/xmldir
	   nxscreate clientds -p exp_c -f1 -l4 -b
	   nxscreate clientds -p hasppXX:10000/expchan/vfcadc_exp/ -f1 -l8  -m -b -s exp_vfc

nxscreate tangods
-----------------

It creates a set of TANGO datasources.

Synopsis
""""""""

.. code:: bash

	  nxscreate tangods [options]

- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default <directory> is '.'
- default <server> is taken from Tango DB
- default <datasource> is 'exp_mot'
- default <host>, <port> are taken from <server>

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

Example
"""""""

.. code:: bash

	   nxscreate tangods -f1 -l2  -p p09/motor/exp. -o exp_mot
	   nxscreate tangods -f1 -l32  -p p02/motor/eh1a. -o exp_mot -b
	   nxscreate tangods -f1 -l32  -p p01/motor/oh1. -o exp_mot -b
	   nxscreate tangods -f1 -l8  -p pXX/slt/exp. -o slt_exp_ -s hasppXX.desy.de -b


nxscreate deviceds
------------------

It creates a set of TANGO datasources for all device attributes.

Synopsis
""""""""

.. code:: bash

	  nxscreate deviceds [options] [dv_attr1 [dv_attr2 [dv_attr3 ...]]]

- without <dv_attr1>: datasources for all attributes are created
- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default <directory> is '.'
- default <server> is taken from Tango DB
- default <datasource> is 'exp_mot'
- default <host>, <port> are taken from <server>

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

Example
"""""""

.. code:: bash

	   nxscreate deviceds  -v p09/pilatus/haso228k
	   nxscreate deviceds  -v p09/lambda2m/haso228k  -s haslambda -b
	   nxscreate deviceds  -v p09/pilatus300k/haso228k -b -o pilatus300k_ RoI Energy ExposureTime


nxscreate onlineds
------------------

It creates a set of motor datasources from an online xml file.

Synopsis
""""""""

.. code:: bash

	  nxscreate onlineds [options] inputFile

- with -b: datasources are created in Configuration Server database
- with -d <directory>: datasources are created on the local filesystem
- without -b or -d <directory>: run in the test mode
- default <inputFile> is '/online_dir/online.xml'
- default <server> is taken from Tango DB

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
  -p XMLPACKAGE, --xml-package=XMLPACKAGE
                        xml template package

Example
"""""""

.. code:: bash

	   nxscreate onlineds -b
	   nxscreate onlineds -d /home/user/xmldir
	   nxscreate onlineds


nxscreate onlinecp
------------------

It creates a detector component from the online.xml file
and its set of datasources.

Synopsis
""""""""

.. code:: bash

	  nxscreate onlinecp [options] inputFile

- without '-c <component>': show a list of possible components
- without '-d <dircetory>:  components are created in Configuration Server database
- with -d <directory>: components are created on the local filesystem
- default <inputFile> is '/online_dir/online.xml'
- default <server> is taken from Tango DB


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
  -p XMLPACKAGE, --xml-package=XMLPACKAGE
                        xml template package

Example
"""""""

.. code:: bash

	  nxscreate onlinecp
	  nxscreate onlinecp -c pilatus
	  nxscreate onlinecp -c lambda -d /home/user/xmldir/


nxscreate stdcomp
------------------

It creates a standard component from the xml template files
and its set of datasources.

Synopsis
""""""""

.. code:: bash

	  nxscreate stdcomp [options] [name1 value1 [name2 value2] ...]

- without '-t <type>': show a list of possible component types
- with '-t <type>  and without -c <component>: show a list of component variables for the given component type
- without '-d <dircetory>:  components are created in Configuration Server database
- with -d <directory>: components are created on the local filesystem
- [name1 value1 [name2 value2] ...] sequence  defines component variable values 

Options:
  -h, --help            show this help message and exit
  -c COMPONENT, --component=COMPONENT
                        component name
  -t CPTYPE, --type=CPTYPE
                        component type
  -r SERVER, --server=SERVER
                        configuration server device name
  -p XMLPACKAGE, --xml-package=XMLPACKAGE
                        xml template package
  -n, --nolower         do not change aliases into lower case
  -o, --overwrite       overwrite existing component
  -d DIRECTORY, --directory=DIRECTORY
                        output directory where datasources will be stored. If
                        it is not set components are stored in Configuration
                        Server database
  -x FILE, --file-prefix=FILE
                        file prefix, i.e. counter

			
Example
"""""""

.. code:: bash

          nxscreate stdcomp  
          nxscreate stdcomp -t slit 
          nxscreate stdcomp -t slit -c front_slit1 xgap slt1x ygap slt1y


nxscreate comp
--------------

It creates a set of simple components.

Synopsis
""""""""

.. code:: bash

	  nxscreate comp [options] [name1] [name2] ...

- with -b: datasources are created in Configuration Server database
- without -b: datasources are created on the local filesystem in -d <directory>
- default <directory> is '.'
- default <server> is taken from Tango DB
- default <strategy> is step
- default <type> is NX_FLOAT
- default <chunk> is SCALAR
- default <nexuspath> is '/entry$var.serialno:NXentry/instrument/collection/

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

Example
"""""""

.. code:: bash

	  nxscreate comp  counter
	  nxscreate comp -f1 -l3 -p exp_c -b
	  nxscreate comp -c lambda -d /home/user/xmldir/
	  nxscreate comp -n '/entry$var.serialno:NXentry/instrument/sis3302:NXdetector/collection:NXcollection/' -p sis3302_1_roi -f1 -l4  -s STEP -t NX_FLOAT64 -k -b -m
	  nxscreate comp -n '/entry$var.serialno:NXentry/instrument/eh1_mca01:NXdetector/data' eh1_mca01 -s STEP -t NX_FLOAT64 -i -b -c SPECTRUM
