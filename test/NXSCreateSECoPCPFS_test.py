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
# \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import random
import struct
import binascii
import shutil

try:
    import tango
except Exception:
    import PyTango as tango

# import nxstools
from nxstools import nxscreate

# try:
#     import nxsextrasp00
# except ImportError:
#     from . import nxsextrasp00


try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

# try:
#     import TestServerSetUp
# except ImportError:
#     from . import TestServerSetUp


if sys.version_info > (3,):
    unicode = str
    long = int


# if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)


# test fixture
class NXSCreateSECoPCPFSTest(unittest.TestCase):

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        try:
            # random seed
            self.seed = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            # random seed
            self.seed = long(time.time() * 256)  # use fractional seconds

        self._rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'

        # home = expanduser("~")
        db = tango.Database()
        self.host = db.get_db_host().split(".")[0]
        self.port = db.get_db_port()
        self.directory = "."
        self.flags = "-d . "
        # self.flags = " -d -r testp09/testmcs/testr228 "
        self.device = 'testp09/testmcs/testr228'
        self.maxDiff = None

    # sets xmlconfiguration
    # \param xmlc configuration instance
    # \param xml xml configuration string
    def setXML(self, xmlc, xml):
        xmlc.XMLString = xml

    # gets xmlconfiguration
    # \param xmlc configuration instance
    # \returns xml configuration string
    def getXML(self, xmlc):
        return xmlc.XMLString

    # test starter
    # \brief Common set up
    def setUp(self):
        print("\nsetting up...")
        print("SEED = %s" % self.seed)

    # test closer
    # \brief Common tear down
    def tearDown(self):
        print("tearing down ...")

    def dsexists(self, name):
        return os.path.isfile("%s/%s.ds.xml" % (self.directory, name))

    def cpexists(self, name):
        return os.path.isfile("%s/%s.xml" % (self.directory, name))

    def getds(self, name):
        with open("%s/%s.ds.xml" % (self.directory, name), 'r') as fl:
            xml = fl.read()
        return xml

    def getcp(self, name):
        with open("%s/%s.xml" % (self.directory, name), 'r') as fl:
            xml = fl.read()
        return xml

    def deleteds(self, name):
        os.remove("%s/%s.ds.xml" % (self.directory, name))

    def deletecp(self, name):
        os.remove("%s/%s.xml" % (self.directory, name))

    def runtest(self, argv):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        nxscreate.main()
        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er

    def runtestexcept(self, argv, exception):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()

        old_argv = sys.argv
        sys.argv = argv
        try:
            error = False
            nxscreate.main()
            etxt = None
        except exception as e:
            error = True
            etxt = str(e)
        self.assertEqual(error, True)

        sys.argv = old_argv

        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        return vl, er, etxt

    # Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error = False
            method(*args, **kwargs)
        except exception:
            error = True
        self.assertEqual(error, True)

    def checkxmls(self, args, fname):
        """ check xmls of components and datasources
        """

        dstotest = []
        cptotest = []
        try:
            for arg in args:
                skip = False
                for cp in arg[1][0]:
                    if self.cpexists(cp):
                        skip = True
                for ds in arg[1][1]:
                    if self.dsexists(ds):
                        skip = True
                if not skip:
                    for ds in arg[1][1]:
                        dstotest.append(ds)
                    for cp in arg[1][0]:
                        cptotest.append(cp)

                    for cmd in arg[0]:
                        vl, er = self.runtest(cmd)
                        # print(vl)
                        # print(er)
                        if er:
                            self.assertTrue(er.startswith("Info: "))
                        else:
                            self.assertEqual('', er)
                        self.assertTrue(vl)

                        for i, ds in enumerate(arg[1][1]):
                            xml = self.getds(ds)
                            self.assertEqual(arg[2][1][i], xml)
                        for i, cp in enumerate(arg[1][0]):
                            xml = self.getcp(cp)
                            self.assertEqual(arg[2][0][i], xml)

                        for ds in arg[1][1]:
                            self.deleteds(ds)
                        for cp in arg[1][0]:
                            self.deletecp(cp)

        finally:
            os.remove(fname)
            for cp in cptotest:
                if self.cpexists(cp):
                    self.deletecp(cp)
            for ds in dstotest:
                if self.dsexists(ds):
                    self.deleteds(ds)

    def test_secopcp_list_none(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        xml = """{}"""
        args = [
            [
                ('nxscreate secopcp -l -j %s %s'
                 % (fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        with open(fname, "w") as fl:
            fl.write(xml)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                # if er:
                #     self.assertTrue(er.startswith("Info: ")
                # else:
                #     self.assertEqual('', er)
                self.assertTrue(not vl)
        finally:
            os.remove(fname)

    def test_secopcp_list_mouldes(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        args = [
            [
                ('nxscreate secopcp -l -j %s %s'
                 % (fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        shutil.copy("test/files/secop.conf", fname)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                # if er:
                #     self.assertTrue(er.startswith("Info: ")
                # else:
                #     self.assertEqual('', er)
                lines = vl.split("\n")
                self.assertEqual(len(lines), 3)
                self.assertEqual(lines[-3], "MODULES:")
                self.assertEqual(
                    lines[-2].split(),
                    ['force', 'drv', 'transducer', 'res', 'T'])
                self.assertEqual(
                    lines[-1].split(),
                    [])
        finally:
            os.remove(fname)

    def ttest_secopcp_create(self):
        """ test nxsccreate stdcomp file system
        """
        fun = sys._getframe().f_code.co_name
        print("Run: %s.%s() " % (self.__class__.__name__, fun))

        fname = '%s/%s%s.json' % (
            os.getcwd(), self.__class__.__name__, fun)

        args = [
            [
                ('nxscreate secopcp  -j %s %s'
                 % (fname, self.flags)).split(),
            ],
        ]

        if os.path.isfile(fname):
            raise Exception("Test file %s exists" % fname)
        shutil.copy("test/files/secop.conf", fname)
        try:
            for arg in args:
                vl, er = self.runtest(arg[0])

                # if er:
                #     self.assertTrue(er.startswith("Info: ")
                # else:
                #     self.assertEqual('', er)
                # lines = vl.split("\n")
                # self.assertEqual(len(lines),3)
                # self.assertEqual(lines[-3], "MODULES:")
                # self.assertEqual(
                #     lines[-2].split(),
                #     ['force', 'drv', 'transducer', 'res', 'T'])
                # self.assertEqual(
                #     lines[-1].split(),
                #     [])
        finally:
            os.remove(fname)


if __name__ == '__main__':
    unittest.main()
