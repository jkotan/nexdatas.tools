Welcome to nxstools's documentation!
====================================

Authors: Jan Kotanski

------------
Introduction
------------

Configuration tools for NeXDaTaS Tango Servers consists of the following command-line scripts:

- `nxscollect <https://nexdatas.github.io/tools/nxscollect.html>`__ uploads external images into the NeXus/HDF5 file
- `nxsconfig <https://nexdatas.github.io/tools/nxsconfig.html>`__ reads NeXus Configuration Server settings
- `nxscreate <https://nexdatas.github.io/tools/nxscreate.html>`__ creates NeXus Configuration components
- `nxsdata <https://nexdatas.github.io/tools/nxsdata.html>`__ runs NeXus Data Writer
- `nxsfileinfo <https://nexdatas.github.io/tools/nxsfileinfo.html>`__ shows nedadata of the NeXus/HDF5 file
- `nxsetup <https://nexdatas.github.io/tools/nxsetup.html>`__ setups NeXDaTaS Tango Server environment

as well as the `nxstools <https://nexdatas.github.io/tools/nxstools.html>`__ package which allows perform these operations
directly from a python code.

| Source code: https://github.com/nexdatas/tools
| Web page: https://nexdatas.github.io/tools
| NexDaTaS Web page: https://nexdatas.github.io

------------
Installation
------------

Install the dependencies:

|    PyTango, sphinx

From sources
""""""""""""

Download the latest NXS Tools version from

|    https://github.com/nexdatas/tools

Extract sources and run

.. code-block:: console

	  $ python setup.py install

Debian packages
"""""""""""""""

Debian `bullseye`, `buster`, `stretch`  or Ubuntu `focal`, `bionic` packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code-block:: console

	  $ sudo su
	  $ curl -s http://repos.pni-hdri.de/debian_repo.pub.gpg | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/debian-hdri-repo.gpg --import
	  $ chmod 644 /etc/apt/trusted.gpg.d/debian-hdri-repo.gpg

and then download the corresponding source list

.. code-block:: console

	  $ cd /etc/apt/sources.list.d
	  $ wget http://repos.pni-hdri.de/bullseye-pni-hdri.list

To install nxstools scripts

.. code-block:: console

	  $ apt-get update
	  $ apt-get install nxstools

or

.. code-block:: console

	  $ apt-get update
	  $ apt-get install nxstools3

for older python3 releases.

To install only the python3 package

.. code-block:: console

	  $ apt-get update
	  $ apt-get install python3-nxstools

and for python2

.. code-block:: console

	  $ apt-get update
	  $ apt-get install python-nxstools

if exists.


From pip
""""""""

To install it from pip you can

.. code-block:: console

   $ python3 -m venv myvenv
   $ . myvenv/bin/activate

   $ pip install nxstools

Moreover it is also good to install

.. code-block:: console

   $ pip install pytango
