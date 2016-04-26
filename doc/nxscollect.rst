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



