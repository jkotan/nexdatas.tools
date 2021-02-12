=========
nxcollect
=========

Description
-----------

The nxscollect is  a command-line tool dedicated to collect detector images.


The append sub-commnand adds images of external formats into the NeXus master file.
The images to collect should be denoted by postrun fields inside NXcollection groups or given by command-line parameters.

The link sub-commnand creates external or internal link in the NeXus master file to NeXus data files.


Synopsis for nxscollect append
------------------------------

.. code:: bash

          nxscollect append [-h] [-c COMPRESSION] [-p PATH] [-i INPUTFILES]
                         [--separator SEPARATOR] [--dtype DATATYPE]
                         [--shape SHAPE] [-s] [-r] [--test] [--h5py]
                         [--h5cpp]
                         [nexus_file [nexus_file ...]]


  nexus_file            nexus files to be collected

Options:
  -h, --help            show this help message and exit
  -c COMPRESSION, --compression COMPRESSION
                        deflate compression rate from 0 to 9 (default: 2) or
                        <filterid>:opt1,opt2,... e.g. -c 32008:0,2 for
                        bitshuffle with lz4
  -p PATH, --path PATH  nexus path for the output field, e.g.
                        /scan/instrument/pilatus/data
  -i INPUTFILES, --input_files INPUTFILES
                        input data files defined with a pattern or separated
                        by ',' e.g.'scan_%05d.tif:0:100'
  --separator SEPARATOR
                        input data files separator (default: ',')
  --dtype DATATYPE      datatype of input data - only for raw data, e.g.
                        'uint8'
  --shape SHAPE         shape of input data - only for raw data, e.g.
                        '[4096,2048]'
  -s, --skip_missing    skip missing files
  -r, --replace_nexus_file
                        if it is set the old file is not copied into a file
                        with .__nxscollect__old__* extension
  --test                execute in the test mode
  --h5py                use h5py module as a nexus reader/writer
  --h5cpp               use h5cpp module as a nexus reader/writer

Examples of nxscollect append
-----------------------------

.. code:: bash

       nxscollect append -c1 /tmp/gpfs/raw/scan_234.nxs

       nxscollect append -c32008:0,2 /ramdisk/scan_123.nxs

       nxscollect append --test /tmp/gpfs/raw/scan_234.nxs

       nxscollect append scan_234.nxs --path /scan/instrument/pilatus/data  --inputfiles 'scan_%05d.tif:0:100'
  

Synopsis for nxscollect link
----------------------------

.. code:: bash

          nxscollect link [-h] [-n NAME] [-t TARGET] [-r] [--test]
                       [--h5py] [--h5cpp]
                       [nexus_file_path]

  nexus_file_path       nexus files with the nexus directory to place the link

Options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  link name
  -t TARGET, --target TARGET
                        link target with the file name if external
  -r, --replace_nexus_file
                        if it is set the old file is not copied into a file
                        with .__nxscollect__old__* extension
  --test                execute in the test mode
  --h5py                use h5py module as a nexus reader/writer
  --h5cpp               use h5cpp module as a nexus reader

  

Examples of nxscollect link
---------------------------

.. code:: bash
       
       nxscollect link scan_234.nxs://entry/instrument/lambda --name data --target lambda.nxs://entry/data/data

       nxscollect link scan_123.nxs://entry:NXentry/instrument/eiger:NXdetector  --target eiger.nxs://entry/data/data
       
