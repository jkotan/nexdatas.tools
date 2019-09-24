#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2018 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
# \package test nexdatas
# \file runtest.py
# the unittest runner
#

import os
import sys

try:
    __import__("PyTango")
    # if module PyTango avalable
    PYTANGO_AVAILABLE = True
except ImportError as e:
    PYTANGO_AVAILABLE = False
    print("PyTango is not available: %s" % e)

try:
    try:
        __import__("pni.io.nx.h5")
    except Exception:
        __import__("pni.nx.h5")
    # if module pni avalable
    PNI_AVAILABLE = True
except ImportError as e:
    PNI_AVAILABLE = False
    print("pni is not available: %s" % e)

try:
    __import__("h5py")
    # if module pni avalable
    H5PY_AVAILABLE = True
except ImportError as e:
    H5PY_AVAILABLE = False
    print("h5py is not available: %s" % e)

try:
    __import__("pninexus.h5cpp")
    # if module pni avalable
    H5CPP_AVAILABLE = True
except ImportError as e:
    H5CPP_AVAILABLE = False
    print("h5cpp is not available: %s" % e)
except SystemError as e:
    H5CPP_AVAILABLE = False
    print("h5cpp is not available: %s" % e)


import unittest

import NXSToolsTest

if not PNI_AVAILABLE and not H5PY_AVAILABLE and not H5CPP_AVAILABLE:
    raise Exception("Please install h5py, h5cpp or pni")

# if PNI_AVAILABLE:
# if H5PY_AVAILABLE:
# if PNI_AVAILABLE and H5PY_AVAILABLE:


# list of available databases
DB_AVAILABLE = []

try:
    import MySQLdb
    # connection arguments to MYSQL DB
    args = {}
    args["db"] = 'tango'
    args["host"] = 'localhost'
    args["read_default_file"] = '/etc/mysql/my.cnf'
    # inscance of MySQLdb
    mydb = MySQLdb.connect(**args)
    mydb.close()
    DB_AVAILABLE.append("MYSQL")
except Exception as e1:
    try:
        import MySQLdb
        from os.path import expanduser
        home = expanduser("~")
        # connection arguments to MYSQL DB
        cnffile = '%s/.my.cnf' % home
        args2 = {
            'host': u'localhost', 'db': u'tango',
            'read_default_file': '%s/.my.cnf' % home,
            'use_unicode': True}
        # inscance of MySQLdb
        mydb = MySQLdb.connect(**args2)
        mydb.close()
        DB_AVAILABLE.append("MYSQL")
    except ImportError as e2:
        print("MYSQL not available: %s %s" % (e1, e2))
    except Exception as e2:
        print("MYSQL not available: %s %s" % (e1, e2))
    except Exception:
        print("MYSQL not available")


try:
    import psycopg2
    # connection arguments to PGSQL DB
    args = {}
    args["database"] = 'mydb'
    # inscance of psycog2
    pgdb = psycopg2.connect(**args)
    pgdb.close()
    DB_AVAILABLE.append("PGSQL")
except ImportError as e:
    print("PGSQL not available: %s" % e)
except Exception as e:
    print("PGSQL not available: %s" % e)
except Exception:
    print("PGSQL not available")


try:
    import cx_Oracle
    # pwd
    passwd = open(
        '%s/pwd' % os.path.dirname(NXSToolsTest.__file__)).read()[:-1]

    # connection arguments to ORACLE DB
    args = {}
    args["dsn"] = (
        "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=dbsrv01.desy.de)"
        "(PORT=1521))(LOAD_BALANCE=yes)(CONNECT_DATA=(SERVER=DEDICATED)"
        "(SERVICE_NAME=desy_db.desy.de)(FAILOVER_MODE=(TYPE=NONE)"
        "(METHOD=BASIC)(RETRIES=180)(DELAY=5))))")
    args["user"] = "read"
    args["password"] = passwd
    # inscance of cx_Oracle
    ordb = cx_Oracle.connect(**args)
    ordb.close()
    DB_AVAILABLE.append("ORACLE")
except ImportError as e:
    print("ORACLE not available: %s" % e)
except Exception as e:
    print("ORACLE not available: %s" % e)
except Exception:
    print("ORACLE not available")

# db = PyTango.Database()

if PNI_AVAILABLE:
    import FileWriterTest
    import PNIWriterTest
    import NXSCollectPNITest
    import NXSFileInfoPNITest
if H5PY_AVAILABLE:
    import H5PYWriterTest
    import FileWriterH5PYTest
    import NXSCollectH5PYTest
    import NXSFileInfoH5PYTest
if H5CPP_AVAILABLE:
    import H5CppWriterTest
    import FileWriterH5CppTest
    import NXSCollectH5CppTest
    import NXSFileInfoH5CppTest
if PNI_AVAILABLE and H5PY_AVAILABLE:
    import FileWriterPNIH5PYTest
# if PNI_AVAILABLE and H5CPP_AVAILABLE:
#     import FileWriterPNIH5CppTest

if H5CPP_AVAILABLE or H5PY_AVAILABLE or H5CPP_AVAILABLE:
    import NXSCollectTest
    import NXSFileInfoTest


if PYTANGO_AVAILABLE:
    import NXSCreateClientDSFSTest
    import NXSCreateClientDSFS2Test
    import NXSCreateClientDSFS3Test
    import NXSCreateTest
    import NXSCreateCompareTest

    import NXSCreateTangoDSFSTest
    import NXSCreateTangoDSFS2Test
    import NXSCreateTangoDSFS3Test

    import NXSCreateDeviceDSFSTest
    import NXSCreateDeviceDSFS2Test
    import NXSCreateDeviceDSFS3Test

    import NXSCreateCompFSTest
    import NXSCreateCompFS2Test
    import NXSCreateCompFS3Test

    import NXSCreateOnlineDSFSTest
    import NXSCreateOnlineDSFS2Test
    import NXSCreateOnlineDSFS3Test

    import NXSCreateOnlineCPFSTest
    import NXSCreateOnlineCPFS2Test
    import NXSCreateOnlineCPFS3Test

    import NXSCreatePoolDSFSTest
    import NXSCreatePoolDSFS2Test
    import NXSCreatePoolDSFS3Test

    if "MYSQL" in DB_AVAILABLE:
        import NXSetUpTest

        import NXSCreateStdCompFSTest
        import NXSCreateStdCompFS2Test
        import NXSCreateStdCompFS3Test

        import NXSConfigTest
        import NXSCreateClientDSDBTest
        import NXSCreateClientDSDB2Test
        import NXSCreateClientDSDBRTest
        import NXSCreateClientDSDBR2Test

        import NXSCreateTangoDSDBTest
        import NXSCreateTangoDSDB2Test
        import NXSCreateTangoDSDBRTest
        import NXSCreateTangoDSDBR2Test

        import NXSCreateCompDBTest
        import NXSCreateCompDB2Test
        import NXSCreateCompDBRTest
        import NXSCreateCompDBR2Test

        import NXSCreateDeviceDSDBTest
        import NXSCreateDeviceDSDB2Test
        import NXSCreateDeviceDSDBRTest
        import NXSCreateDeviceDSDBR2Test
        import NXSCreateDeviceDSFS4Test

        import NXSCreateOnlineDSDBTest
        import NXSCreateOnlineDSDB2Test
        import NXSCreateOnlineDSDBRTest
        import NXSCreateOnlineDSDBR2Test
        import NXSCreateOnlineDSDBETest
        import NXSCreateOnlineDSDBE2Test

        import NXSCreateOnlineCPDBTest
        import NXSCreateOnlineCPDB2Test
        import NXSCreateOnlineCPDBRTest
        import NXSCreateOnlineCPDBR2Test

        import NXSCreateStdCompDBTest
        import NXSCreateStdCompDB2Test
        import NXSCreateStdCompDBRTest
        import NXSCreateStdCompDBR2Test
        import NXSCreateStdCompDBETest
        import NXSCreateStdCompDBE2Test

        import NXSCreatePoolDSDBTest
        import NXSCreatePoolDSDB2Test
        import NXSCreatePoolDSDBRTest
        import NXSCreatePoolDSDBR2Test


# main function
def main():

    # test suit
    suite = unittest.TestSuite()

    if PNI_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(FileWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(PNIWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectPNITest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSFileInfoPNITest))

    if H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(FileWriterH5PYTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5PYWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectH5PYTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSFileInfoH5PYTest))
    if H5CPP_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterH5CppTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(H5CppWriterTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectH5CppTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSFileInfoH5CppTest))
    if PNI_AVAILABLE and H5PY_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                FileWriterPNIH5PYTest))

    if H5CPP_AVAILABLE or H5PY_AVAILABLE or H5CPP_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCollectTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSFileInfoTest))

    if PYTANGO_AVAILABLE:
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateClientDSFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateClientDSFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateClientDSFS3Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateCompareTest))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateTangoDSFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateTangoDSFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateTangoDSFS3Test))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineDSFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineDSFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineDSFS3Test))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineCPFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineCPFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateOnlineCPFS3Test))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreatePoolDSFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreatePoolDSFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreatePoolDSFS3Test))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateDeviceDSFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateDeviceDSFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateDeviceDSFS3Test))

        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateCompFSTest))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateCompFS2Test))
        suite.addTests(
            unittest.defaultTestLoader.loadTestsFromModule(
                NXSCreateCompFS3Test))
        if "MYSQL" in DB_AVAILABLE:
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSetUpTest))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSConfigTest))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompFSTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompFS2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompFS3Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateClientDSDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateClientDSDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateClientDSDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateClientDSDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateTangoDSDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateTangoDSDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateTangoDSDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateTangoDSDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineCPDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineCPDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineCPDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineCPDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDBETest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateOnlineDSDBE2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDBETest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateStdCompDBE2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreatePoolDSDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreatePoolDSDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreatePoolDSDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreatePoolDSDBR2Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateDeviceDSDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateDeviceDSDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateDeviceDSDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateDeviceDSDBR2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateDeviceDSFS4Test))

            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateCompDBTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateCompDB2Test))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateCompDBRTest))
            suite.addTests(
                unittest.defaultTestLoader.loadTestsFromModule(
                    NXSCreateCompDBR2Test))

    # test runner
    runner = unittest.TextTestRunner()
    # test result
    result = runner.run(suite).wasSuccessful()
    sys.exit(not result)

    #   if ts:
    #       ts.tearDown()


if __name__ == "__main__":
    main()
