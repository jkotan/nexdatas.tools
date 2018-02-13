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
## \package test nexdatas
## \file XMLConfiguratorTest.py
# unittests for field Tags running Tango Server
#
import unittest
import os
import sys
import subprocess
import random
import struct
import binascii
import time
import threading
import json
import PyTango
import ServerSetUp
import subprocess
from nxstools import nxsconfig
import sys
from cStringIO import StringIO

class mytty(object):
    def __init__(self, underlying):
#        underlying.encoding = 'cp437'
        self.__underlying = underlying
    def __getattr__(self, name):
        return getattr(self.__underlying, name)
    def isatty(self):
        return True

## if 64-bit machione
IS64BIT = (struct.calcsize("P") == 8)

#from nxsconfigserver.XMLConfigurator  import XMLConfigurator
#from nxsconfigserver.Merger import Merger
#from nxsconfigserver.Errors import (NonregisteredDBRecordError, UndefinedTagError,
#                                     IncompatibleNodeError)
# import nxsconfigserver

def myinput(w, text):
    myio = os.fdopen(w, 'w')
    myio.write(text)

    #myio.close()

## test fixture
class NXSConfigTest(unittest.TestCase):

    ## constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

        self.helperror = "Error: too few arguments\n"

        self.helpinfo = """usage: nxsconfig [-h]
                 {list,show,get,delete,variables,sources,record,merge,components,data,describe,info,geometry,servers}
                 ...

Command-line tool for reading NeXus configuration from NXSConfigServer

positional arguments:
  {list,show,get,delete,variables,sources,record,merge,components,data,describe,info,geometry,servers}
                        sub-command help
    list                list names of available components (or datasources)
    show                show components (or datasources) with given names
    get                 get full configuration of components (or datasources)
    delete              delete components (or datasources) with given names
    variables           get a list of component variables
    sources             get a list of component datasources
    record              get a list of datasource record names for components
                        or datasources
    merge               get merged configuration of components (or
                        datasources)
    components          get a list of dependent components
    data                get/set values of component variables
    describe            show all parameters of given components (or
                        datasources)
    info                show source parameters of given components (or
                        datasources)
    geometry            show transformation parameters of given components (or
                        datasources)
    servers             get a list of configuration servers from the current
                        tango host

optional arguments:
  -h, --help            show this help message and exit

For more help:
  nxsconfig <sub-command> -h

"""

        try:
            # random seed
            self.seed  = long(binascii.hexlify(os.urandom(16)), 16)
        except NotImplementedError:
            import time
            ## random seed
            self.seed  = long(time.time() * 256) # use fractional seconds

        self.__rnd = random.Random(self.seed)

        self._bint = "int64" if IS64BIT else "int32"
        self._buint = "uint64" if IS64BIT else "uint32"
        self._bfloat = "float64" if IS64BIT else "float32"

        self.__args = '{"host":"localhost", "db":"nxsconfig", ' \
                      '"read_default_file":"/etc/my.cnf", "use_unicode":true}'
        self.__cmps = []
        self.__ds = []
        self.__man = []
        self.children = ("record", "doc", "device", "database", "query",
                         "datasource", "result")

        from os.path import expanduser
        home = expanduser("~")
        self.__args2 = '{"host":"localhost", "db":"nxsconfig", ' \
                       '"read_default_file":"%s/.my.cnf", ' \
                       '"use_unicode":true}' % home
        self._sv = ServerSetUp.ServerSetUp()

    # opens config server
    # \param args connection arguments
    # \returns NXSConfigServer instance
    def openConfig(self, args):

        found = False
        cnt = 0
        while not found and cnt < 1000:
            try:
                print "\b.",
                xmlc = PyTango.DeviceProxy(
                    self._sv.new_device_info_writer.name)
                time.sleep(0.01)
                if xmlc.state() == PyTango.DevState.ON:
                    found = True
                found = True
            except Exception, e:
                print self._sv.new_device_info_writer.name, e
                found = False
            except:
                found = False

            cnt += 1

        if not found:
            raise Exception(
                "Cannot connect to %s"
                % self._sv.new_device_info_writer.name)

        if xmlc.state() == PyTango.DevState.ON:
            xmlc.JSONSettings = args
            xmlc.Open()
        version = xmlc.version
        vv = version.split('.')
        self.revision = long(vv[-1])
        self.version = ".".join(vv[0:3])
        self.label = ".".join(vv[3:-1])


        self.assertEqual(xmlc.state(), PyTango.DevState.OPEN)
        return xmlc

    # closes opens config server
    # \param xmlc XMLConfigurator instance
    def closeConfig(self, xmlc):
        self.assertEqual(xmlc.state(), PyTango.DevState.OPEN)

        xmlc.Close()
        self.assertEqual(xmlc.state(), PyTango.DevState.ON)

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


    ## test starter
    # \brief Common set up
    def setUp(self):
        print "\nsetting up..."
        self._sv.setUp()
        print "SEED =", self.seed

    ## test closer
    # \brief Common tear down
    def tearDown(self):
        print "tearing down ..."
        if self.__cmps:
            el = self.openConf()
            for cp in self.__cmps:
                el.deleteComponent(cp)
            el.close()
        if self.__ds:
            el = self.openConf()
            for ds in self.__ds:
                el.deleteDataSource(ds)
            el.close()

        if self.__man:
            el = self.openConf()
            el.setMandatoryComponents(self.__man)
            el.close()
        self._sv.tearDown()

    def openConf(self):
        try:
            el = self.openConfig(self.__args)
        except:
            el = self.openConfig(self.__args2)
        return el

    ## Exception tester
    # \param exception expected exception
    # \param method called method
    # \param args list with method arguments
    # \param kwargs dictionary with method arguments
    def myAssertRaise(self, exception, method, *args, **kwargs):
        try:
            error =  False
            method(*args, **kwargs)
        except :
            error = True
        self.assertEqual(error, True)


    ## sets selection configuration
    # \param selectionc configuration instance
    # \param selection selection configuration string
    def setSelection(self, selectionc, selection):
        selectionc.selection = selection

    ## gets selectionconfiguration
    # \param selectionc configuration instance
    # \returns selection configuration string
    def getSelection(self, selectionc):
        return selectionc.selection

    ## open close test test
    # \brief It tests XMLConfigurator
    def ttest_openClose(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        xmlc = self.openConf()
        self.assertEqual(long(xmlc.version.split('.')[-1]), self.revision)
        label = 'asdd@aff.asdf'
        if hasattr(xmlc,"versionLabel"):
            xmlc.versionLabel = label
        self.assertEqual(long(xmlc.version.split('.')[-1]), self.revision)
        if hasattr(xmlc,"versionLabel"):
            self.assertEqual(".".join(xmlc.version.split('.')[3:-1]),label)
        xmlc.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = mystdout = StringIO()
        sys.stderr = mystderr = StringIO()
        old_argv = sys.argv
        sys.argv = ['nxsconfig']
        with self.assertRaises(SystemExit):
            nxsconfig.main()

        sys.argv = old_argv
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        vl = mystdout.getvalue()
        er = mystderr.getvalue()
        self.assertEqual(self.helpinfo, vl)
        self.assertEqual(self.helperror, er)

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_help(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        helps = ['-h', '--help']
        for hl in helps:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = ['nxsconfig', hl]
            with self.assertRaises(SystemExit):
                nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()
    #        print vl
    #        print len(vl), vl[-2], ord(vl[-1])
    #        print len(self.helpinfo), ord(self.helpinfo[-2]), ord(self.helpinfo[-1])
            self.assertEqual(self.helpinfo[0:-1], vl)
            self.assertEqual('', er)


    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_list_comp_available(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            ('nxsconfig list -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            if "-n" in cmd or "--no-newlines" in cmd:
                avc3 = [ec.strip() for ec in vl.split(' ') if ec.strip()]
            else:
                avc3 = vl.split('\n')

            for cp in avc3:
                if cp:
                    self.assertTrue(cp in avc2)

            for cp in avc2:
                if not cp.startswith("__"):
                    self.assertTrue(cp in avc3)

            self.assertEqual('', er)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_comp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

        commands = [
            ('nxsconfig delete -f  -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -f  --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            self.setXML(el, xml2)
            self.assertEqual(el.storeComponent(name2), None)
            self.__cmps.append(name2)
            avc2 = el.availableComponents()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()
            avc3 = el.availableComponents()
            self.assertEqual((list(set(avc2) - set(avc3))), [name2])


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        el.close()


    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_ds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)

        commands = [
            ('nxsconfig delete -f -d -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -f -d --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -f --datasource -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -f --datasource --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            self.setXML(el, xml2)
            self.assertEqual(el.storeDataSource(name2), None)
            self.__ds.append(name2)
            avc2 = el.availableDataSources()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()
            avc3 = el.availableDataSources()
            self.assertEqual((list(set(avc2) - set(avc3))), [name2])


        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        el.close()


    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_comp_noforce_pipe(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

        commands = [
            ('nxsconfig delete -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['\n','Y\n','y\n'',N\n','n\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeComponent(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableComponents()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                sys.stdin = mystdin = StringIO()
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove Component ')
                self.assertEqual(
                    er,
                    "Error: EOF when reading a line. "
                    "Consider to use the --force option \n")
                avc3 = el.availableComponents()
                self.assertEqual((list(set(avc2) - set(avc3))), [])


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_ds_noforce_pipe(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)

        commands = [
            ('nxsconfig delete -d -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -d --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['\n','Y\n','y\n'',N\n','n\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeDataSource(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableDataSources()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                sys.stdin = mystdin = StringIO()
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove DataSource')
                self.assertEqual(
                    er,
                    "Error: EOF when reading a line. "
                    "Consider to use the --force option \n")
                avc3 = el.availableDataSources()
                self.assertEqual((list(set(avc2) - set(avc3))), [])


        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_comp_noforce(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

        commands = [
            ('nxsconfig delete -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['\n','Y\n','y\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeComponent(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableComponents()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                new_stdin = mytty(os.fdopen(r, 'r'))
                old_stdin, sys.stdin = sys.stdin, new_stdin
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                tm = threading.Timer(1., myinput, [w, ans])
                tm.start()
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove Component ')
                self.assertEqual('', er)
                avc3 = el.availableComponents()
                self.assertEqual((list(set(avc2) - set(avc3))), [name2])


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_ds_noforce(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)

        commands = [
            ('nxsconfig delete -d -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -d --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['\n','Y\n','y\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeDataSource(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableDataSources()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                new_stdin = mytty(os.fdopen(r, 'r'))
                old_stdin, sys.stdin = sys.stdin, new_stdin
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                tm = threading.Timer(1., myinput, [w, ans])
                tm.start()
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove DataSource')
                self.assertEqual('', er)
                avc3 = el.availableDataSources()
                self.assertEqual((list(set(avc2) - set(avc3))), [name2])


        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        el.close()

 
    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_comp_noforce_no(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

        commands = [
            ('nxsconfig delete -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['N\n','n\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeComponent(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableComponents()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                new_stdin = mytty(os.fdopen(r, 'r'))
                old_stdin, sys.stdin = sys.stdin, new_stdin
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                tm = threading.Timer(1., myinput, [w, ans])
                tm.start()
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove Component ')
                self.assertEqual('', er)
                avc3 = el.availableComponents()
                self.assertEqual((list(set(avc2) - set(avc3))), [])


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_delete_ds_noforce_no(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
        #        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)

        commands = [
            ('nxsconfig delete -d -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete -d --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource -s %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
            ('nxsconfig delete --datasource --server %s %s'
             % (self._sv.new_device_info_writer.name, name2)).split(),
        ]
        answers = ['N\n','n\n']
        for cmd in commands:
            for ans in answers:
                self.setXML(el, xml2)
                self.assertEqual(el.storeDataSource(name2), None)
                self.__cmps.append(name2)
                avc2 = el.availableDataSources()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                old_stdin = sys.stdin
                r, w = os.pipe()
                new_stdin = mytty(os.fdopen(r, 'r'))
                old_stdin, sys.stdin = sys.stdin, new_stdin
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                tm = threading.Timer(1., myinput, [w, ans])
                tm.start()
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                sys.stdin = old_stdin
                vl = mystdout.getvalue()
                er = mystderr.getvalue()
                self.assertEqual(vl[:17], 'Remove DataSource')
                self.assertEqual('', er)
                avc3 = el.availableDataSources()
                self.assertEqual((list(set(avc2) - set(avc3))), [])


        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_list_comp_available_private(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "__mcs_test_component__"
        name2 = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1__'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            ('nxsconfig list -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            if "-n" in cmd or "--no-newlines" in cmd:
                avc3 = [ec.strip() for ec in vl.split(' ') if ec.strip()]
            else:
                avc3 = vl.split('\n')

            for cp in avc3:
                if cp:
                    self.assertTrue(cp in avc2)

            for cp in avc2:
                if not cp.startswith("__"):
                    self.assertTrue(cp in avc3)

            self.assertEqual('', er)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_list_comp_available_private2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "__mcs_test_component__"
        name2 = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1__'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            ('nxsconfig list -p -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -p --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --private --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            if "-n" in cmd or "--no-newlines" in cmd:
                avc3 = [ec.strip() for ec in vl.split(' ') if ec.strip()]
            else:
                avc3 = vl.split('\n')

            for cp in avc3:
                if cp:
                    self.assertTrue(cp in avc2)

            for cp in avc2:
                if cp.startswith("__"):
                    self.assertTrue(cp in avc3)

            self.assertEqual('', er)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_list_comp_available_mandatory(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_1'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        self.assertEqual(el.setMandatoryComponents([name]), None)
        man2 = el.mandatoryComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            ('nxsconfig list -m -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -m --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --mandatory --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
        ]
#        commands = [['nxsconfig', 'list']]
        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            if "-n" in cmd or "--no-newlines" in cmd:
                avc3 = [ec.strip() for ec in vl.split(' ') if ec.strip()]
            else:
                avc3 = vl.split('\n')

            for cp in avc3:
                if cp:
                    self.assertTrue(cp in man2)

            for cp in man2:
                self.assertTrue(cp in avc3)

            self.assertEqual('', er)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_list_datasources_available(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><datasource type='TANGO' name='testds1'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><datasource type='CLIENT' name'testds1'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeDataSource(name2), None)
        self.__ds.append(name2)
        avc2 = el.availableDataSources()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.datasources([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            ('nxsconfig list -d -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list -d --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources -n -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources -n --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources --no-newlines  -s %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources --server %s'
             % self._sv.new_device_info_writer.name).split(),
            ('nxsconfig list --datasources --no-newlines  --server %s'
             % self._sv.new_device_info_writer.name).split(),
        ]
        for cmd in commands:
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue()
            er = mystderr.getvalue()

            if "-n" in cmd or "--no-newlines" in cmd:
                avc3 = [ec.strip() for ec in vl.split(' ') if ec.strip()]
            else:
                avc3 = vl.split('\n')

            for cp in avc3:
                if cp:
                    self.assertTrue(cp in avc2)

            for cp in avc2:
                self.assertTrue(cp in avc3)

            self.assertEqual('', er)

        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop(-2)
        self.assertEqual(el.deleteDataSource(name2), None)
        self.__ds.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_show_comp_av(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/>\n</definition>"
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/>$datasources.sl1right</definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig show %s -s %s',
            'nxsconfig show %s --server %s',
            'nxsconfig show %s -s %s',
            'nxsconfig show %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()

                self.assertEqual(vl.strip(), cmps[nm])
                self.assertEqual(er, "")

        for scmd in commands:
            nm = name3
            cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: Component '%s' not stored in the configuration server"
                             % name3)

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()

            self.assertEqual(vl.replace(">\n<", "><").replace("> <", "><"),
                             ("%s\n%s" % (cmps[name], cmps[name2])).replace(
                                 ">\n<", "><").replace("> <", "><"))
            self.assertEqual(er, "")

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name3),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: Component '%s' not stored in the configuration server"
                             % name3)


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_show_datasources_av(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><datasource type='TANGO' name='testds1'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><datasource type='CLIENT' name'testds1'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeDataSource(name2), None)
        self.__ds.append(name2)
        avc2 = el.availableDataSources()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.datasources([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig show %s -d -s %s',
            'nxsconfig show %s -d --server %s',
            'nxsconfig show %s -d -s %s',
            'nxsconfig show %s -d --server %s',
            'nxsconfig show %s --datasources -s %s',
            'nxsconfig show %s --datasources --server %s',
            'nxsconfig show %s --datasources -s %s',
            'nxsconfig show %s --datasources --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()

                self.assertEqual(vl, cmps[nm])
                self.assertEqual(er, "")

        for scmd in commands:
            nm = name3
            cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: DataSource '%s' not stored in the configuration server"
                             % name3)

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()

            self.assertEqual(vl.replace(">\n<", "><").replace("> <", "><"),
                             ("%s\n%s" % (cmps[name], cmps[name2])).replace(
                                 ">\n<", "><").replace("> <", "><"))
            self.assertEqual(er, "")

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name3),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: DataSource '%s' not stored in the configuration server"
                             % name3)


        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop(-2)
        self.assertEqual(el.deleteDataSource(name2), None)
        self.__ds.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_av(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/>\n</definition>"
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/>$datasources.sl1right</definition>"
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                el.createConfiguration(man + [nm])
                cpxml = el.xmlstring
                self.assertEqual(vl.strip(), cpxml)
                self.assertEqual(er, "")

        for scmd in commands:
            nm = name3
            cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: Component '%s' not stored in the configuration server"
                             % name3)

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()
            el.createConfiguration(man + [name, name2])
            cpxml = el.xmlstring
            self.assertEqual(vl.strip(), cpxml)

            self.assertEqual(er, "")

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name3),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue().strip()

            self.assertEqual(vl, "")
            self.assertEqual(er,
                "Error: Component '%s' not stored in the configuration server"
                             % name3)


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_incompnodes_groups(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry' name='test'/>\n</definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2' name='test'/>$datasources.sl1right</definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            with self.assertRaises(SystemExit):
                nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()
            self.assertEqual(vl.strip(), "")

            self.assertTrue(er.startswith('Error: "Incompatible element attributes'))


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_incompnodes_fields(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<definition><field type='NXentry' name='test'/>\n</definition>"
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2' name='test'/>$datasources.sl1right</definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            with self.assertRaises(SystemExit):
                nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()
            self.assertEqual(vl.strip(), "")

            self.assertTrue(er.startswith('Error: "Incompatible element attributes'))


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_incompnodes_tags(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<field type='NXentry' name='test'>\n"
        xml2 = "<?xml version='1.0'?><field type='NXentry' name='test2'>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]

        for scmd in commands:
            cmd = (scmd % ("%s %s" % (name, name2),
                           self._sv.new_device_info_writer.name)).split()
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = mystdout = StringIO()
            sys.stderr = mystderr = StringIO()
            old_argv = sys.argv
            sys.argv = cmd
            with self.assertRaises(SystemExit):
                nxsconfig.main()

            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
#            el.createConfiguration(man + [name, name2])
#            cpxml = el.xmlstring
            vl = mystdout.getvalue().strip()
            er = mystderr.getvalue()
            self.assertEqual(vl.strip(), "")
            self.assertEqual(str(er)[:40], "Error from XML parser: no element found: "[:40])


        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_nods(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        avds = el.availableDataSources()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        dsname = "mcs_test_datasource"
        dsname2 = "mcs_test_datasource2"
        while dsname in avds:
            dsname = dsname + '_1'

        while dsname2 in avds:
            dsname2 = dsname2 + '_2'

        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/>$datasources.%s\n</definition>" % dsname
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/>$datasources.%s</definition>" % dsname2
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}
        dss = {name: dsname, name2: dsname2}
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), "")
                self.assertEqual(er,
                    "Error: Datasource %s not stored in Configuration Server\n" % dss[nm])



        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_nocp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        dsname = "mcs_test_subcp"
        dsname2 = "mcs_test_subcp2"
        while dsname in avc:
            dsname = dsname + '_1'

        while dsname2 in avc:
            dsname2 = dsname2 + '_2'

        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/>$components.%s\n</definition>" % dsname
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/>$components.%s</definition>" % dsname2
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}
        dss = {name: dsname, name2: dsname2}
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), "")
                self.assertEqual(er,
                    "Error: Component %s not stored in Configuration Server\n" % dss[nm])



        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_ds(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        avds = el.availableDataSources()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        dsname = "mcs_test_datasource"
        dsname2 = "mcs_test_datasource2"
        while dsname in avds:
            dsname = dsname + '_1'

        while dsname2 in avds:
            dsname2 = dsname2 + '_2'

        xml = "<?xml version='1.0'?>\n<definition><attribute type='NXentry'>$datasources.%s\n</attribute></definition>" % dsname
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'>$datasources.%s</field></definition>" % dsname2
        dsxml = "<?xml version='1.0'?><definition><datasource name='%s' type='TANGO'><datasource/></datasource></definition>" % dsname
        dsxml2 = "<?xml version='1.0'?><definition><datasource name='%s' type='CLIENT'><datasource/></datasource></definition>" % dsname2
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}
        dss = {name: dsname, name2: dsname2}
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        self.setXML(el, dsxml)
        self.assertEqual(el.storeDataSource(dsname), None)
        self.__ds.append(dsname)
        self.setXML(el, dsxml2)
        self.assertEqual(el.storeDataSource(dsname2), None)
        self.__ds.append(dsname2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                el.createConfiguration(man + [nm])
                cpxml = el.xmlstring
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), cpxml)
                self.assertEqual(er.strip(), "")



        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteDataSource(dsname), None)
        self.__ds.pop(-2)
        self.assertEqual(el.deleteDataSource(dsname2), None)
        self.__ds.pop()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        dsname = "mcs_test_subcp"
        dsname2 = "mcs_test_subcp2"
        while dsname in avc:
            dsname = dsname + '_1'

        while dsname2 in avc:
            dsname2 = dsname2 + '_2'

        xml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/>$components.%s\n</definition>" % dsname
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/>$components.%s</definition>" % dsname2
        dsxml = "<?xml version='1.0'?>\n<definition><group type='NXentry'/><field name='test'/>\n</definition>"
        dsxml2 = "<?xml version='1.0'?><definition><field type='NXentry2'/><field name='test3'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2}
        dss = {name: dsname, name2: dsname2}
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(dsname), None)
        self.__cmps.append(dsname)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(dsname2), None)
        self.__cmps.append(dsname2)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                el.createConfiguration(man + [nm, dss[nm]])
                cpxml = el.xmlstring
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), cpxml)
                self.assertEqual(er,"")



        self.assertEqual(el.deleteComponent(dsname2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(dsname), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_wrongxml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?>\n<group type='NXentry'/>\n</definition>"
        xml2 = "<?xml version='1.0'?><definition<field type='NXentry2'/></definition>"
        xml3 = "<?xml version='1.0'?><definition<field type='NXentry2/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2, name3: xml3}

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        self.setXML(el, xml3)
        self.assertEqual(el.storeComponent(name3), None)
        self.__cmps.append(name3)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), "")
                self.assertTrue(str(er).startswith("Error from XML parser: not well-formed (invalid token):"))



        self.assertEqual(el.deleteComponent(name3), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()


        el.close()

    ## comp_available test
    # \brief It tests XMLConfigurator
    def test_get_comp_wrongdsxml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableComponents()
        avds = el.availableDataSources()
        man = el.mandatoryComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        dsname = "mcs_test_datasource"
        dsname2 = "mcs_test_datasource2"
        dsname3 = "mcs_test_datasource3"
        while dsname in avds:
            dsname = dsname + '_1'

        while dsname2 in avds:
            dsname2 = dsname2 + '_2'
        while dsname3 in avds:
            dsname3 = dsname3 + '_3'

        xml = "<?xml version='1.0'?>\n<definition><attribute type='NXentry'>$datasources.%s\n</attribute></definition>" % dsname
        xml2 = "<?xml version='1.0'?><definition><field type='NXentry2'>$datasources.%s</field></definition>" % dsname2
        xml3 = "<?xml version='1.0'?><definition><field type='NXentry2'>$datasources.%s</field></definition>" % dsname3
        dsxml = "<?xml version='1.0'?><definition><datasource name=%s' type='TANGO'></datasource></definition>" % dsname
        dsxml2 = "<?xml version='1.0'?><definition><datasource name='%s' type='CLIENT'></definition>" % dsname2
        dsxml3 = "<?xml version='1.0'><datasource name='%s' type='CLIENT'></datasource>" % dsname3
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        name3 = name + '_3'
        while name2 in avc:
            name2 = name2 + '_2'
        while name3 in avc:
            name3 = name3 + '_3'
#        print avc
        cmps =  {name: xml, name2: xml2, name3: xml3}
        dss = {name: dsname, name2: dsname2}
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        self.setXML(el, xml3)
        self.assertEqual(el.storeComponent(name3), None)
        self.__cmps.append(name3)
        self.setXML(el, dsxml)
        self.assertEqual(el.storeDataSource(dsname), None)
        self.__ds.append(dsname)
        self.setXML(el, dsxml2)
        self.assertEqual(el.storeDataSource(dsname2), None)
        self.__ds.append(dsname2)
        self.setXML(el, dsxml3)
        self.assertEqual(el.storeDataSource(dsname3), None)
        self.__ds.append(dsname3)
        avc2 = el.availableComponents()
        # print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        commands = [
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
            'nxsconfig get %s -s %s',
            'nxsconfig get %s --server %s',
        ]
        for scmd in commands:
            for nm in cmps.keys():
                cmd = (scmd % (nm, self._sv.new_device_info_writer.name)).split()
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                sys.stdout = mystdout = StringIO()
                sys.stderr = mystderr = StringIO()
                old_argv = sys.argv
                sys.argv = cmd
                with self.assertRaises(SystemExit):
                    nxsconfig.main()

                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                vl = mystdout.getvalue().strip()
                er = mystderr.getvalue()
                self.assertEqual(vl.strip(), "")
                self.assertTrue(str(er).startswith("Error from XML parser:"))



        self.assertEqual(el.deleteComponent(name3), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteDataSource(dsname3), None)
        self.__ds.pop()
        self.assertEqual(el.deleteDataSource(dsname2), None)
        self.__ds.pop()
        self.assertEqual(el.deleteDataSource(dsname), None)
        self.__ds.pop()

    #########################################################

    ##  component test
    # \brief It tests default settings
    def ttest_available_comp_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableComponents()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        cpx = el.components(avc)
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        cpx2 = el.components(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        cpx3 = el.components(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_available_no_comp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableComponents()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.myAssertRaise(NonregisteredDBRecordError,el.components, [name])

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_available_comp_update(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableComponents()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        cpx = el.components(avc)

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        cpx2 = el.components(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        cpx2 = el.components(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml2)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        cpx3 = el.components(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+3)
        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_available_comp2_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableComponents()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        cpx = el.components(avc)

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        cpx2 = el.components(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
#        print avc2
        cpx2 = el.components(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name2 in avc2)
        j = avc2.index(name2)
        self.assertEqual(cpx2[j], xml2)

        cpx2b = el.components([name, name2])
        self.assertEqual(cpx2b[0], xml)
        self.assertEqual(cpx2b[1], xml2)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop(-2)

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        cpx3 = el.components(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+4)
        self.assertEqual(el.close(), None)

    ##  selection test
    # \brief It tests default settings
    def ttest_available_sel_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableSelections()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_selection"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
        print avc
        cpx = el.selections(avc)
        self.setSelection(el, xml)
        self.assertEqual(el.storeSelection(name), None)
        self.__cmps.append(name)
        avc2 = el.availableSelections()
        print avc2
        cpx2 = el.selections(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.assertEqual(el.deleteSelection(name), None)
        self.__cmps.pop()

        avc3 = el.availableSelections()
        cpx3 = el.selections(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ##  selection test
    # \brief It tests default settings
    def ttest_available_no_sel(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableSelections()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_selection"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.myAssertRaise(NonregisteredDBRecordError,el.selections, [name])

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ##  selection test
    # \brief It tests default settings
    def ttest_available_sel_update(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableSelections()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_selection"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        cpx = el.selections(avc)

        self.setSelection(el, xml)
        self.assertEqual(el.storeSelection(name), None)
        self.__cmps.append(name)
        avc2 = el.availableSelections()
#        print avc2
        cpx2 = el.selections(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setSelection(el, xml2)
        self.assertEqual(el.storeSelection(name), None)
        self.__cmps.append(name)
        avc2 = el.availableSelections()
#        print avc2
        cpx2 = el.selections(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml2)

        self.assertEqual(el.deleteSelection(name), None)
        self.__cmps.pop()

        avc3 = el.availableSelections()
        cpx3 = el.selections(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ##  selection test
    # \brief It tests default settings
    def ttest_available_sel2_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableSelections()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_selection"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        cpx = el.selections(avc)

        self.setSelection(el, xml)
        self.assertEqual(el.storeSelection(name), None)
        self.__cmps.append(name)
        avc2 = el.availableSelections()
#        print avc2
        cpx2 = el.selections(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setSelection(el, xml2)
        self.assertEqual(el.storeSelection(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableSelections()
#        print avc2
        cpx2 = el.selections(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name2 in avc2)
        j = avc2.index(name2)
        self.assertEqual(cpx2[j], xml2)

        cpx2b = el.selections([name, name2])
        self.assertEqual(cpx2b[0], xml)
        self.assertEqual(cpx2b[1], xml2)

        self.assertEqual(el.deleteSelection(name), None)
        self.__cmps.pop(-2)

        self.assertEqual(el.deleteSelection(name2), None)
        self.__cmps.pop()

        avc3 = el.availableSelections()
        cpx3 = el.selections(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ## comp_available test
    # \brief It tests XMLConfigurator
    def ttest_dsrc_available(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        avc = el.availableDataSources()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        avc2 = el.availableDataSources()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)
        cpx = el.dataSources([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        avc3 = el.availableDataSources()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ##  dataSource test
    # \brief It tests default settings
    def ttest_available_dsrc_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableDataSources()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        cpx = el.dataSources(avc)
        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        avc2 = el.availableDataSources()
#        print avc2
        cpx2 = el.dataSources(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        avc3 = el.availableDataSources()
        cpx3 = el.dataSources(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        self.assertEqual(el.close(), None)

    ##  dataSource test
    # \brief It tests default settings
    def ttest_available_no_dsrc(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableDataSources()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.myAssertRaise(NonregisteredDBRecordError,el.dataSources, [name])

        self.assertEqual(long(el.version.split('.')[-1]), self.revision)
        self.assertEqual(el.close(), None)

    ##  dataSource test
    # \brief It tests default settings
    def ttest_available_dsrc_update(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableDataSources()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        cpx = el.dataSources(avc)

        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        avc2 = el.availableDataSources()
#        print avc2
        cpx2 = el.dataSources(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setXML(el, xml2)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        avc2 = el.availableDataSources()
#        print avc2
        cpx2 = el.dataSources(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml2)

        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop()

        avc3 = el.availableDataSources()
        cpx3 = el.dataSources(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+3)
        self.assertEqual(el.close(), None)

    ##  dataSource test
    # \brief It tests default settings
    def ttest_available_dsrc2_xml(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()

        avc = el.availableDataSources()
        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_datasource"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><group type='NXentry2'/></definition>"
        while name in avc:
            name = name + '_1'
        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc
        cpx = el.dataSources(avc)

        self.setXML(el, xml)
        self.assertEqual(el.storeDataSource(name), None)
        self.__ds.append(name)
        avc2 = el.availableDataSources()
#        print avc2
        cpx2 = el.dataSources(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name in avc2)
        j = avc2.index(name)
        self.assertEqual(cpx2[j], xml)

        self.setXML(el, xml2)
        self.assertEqual(el.storeDataSource(name2), None)
        self.__ds.append(name2)
        avc2 = el.availableDataSources()
#        print avc2
        cpx2 = el.dataSources(avc2)
        self.assertTrue(isinstance(avc2, list))
        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc2)
            j = avc2.index(avc[i])
            self.assertEqual(cpx2[j], cpx[i])

        self.assertTrue(name2 in avc2)
        j = avc2.index(name2)
        self.assertEqual(cpx2[j], xml2)

        cpx2b = el.dataSources([name, name2])
        self.assertEqual(cpx2b[0], xml)
        self.assertEqual(cpx2b[1], xml2)

        self.assertEqual(el.deleteDataSource(name), None)
        self.__ds.pop(-2)

        self.assertEqual(el.deleteDataSource(name2), None)
        self.__ds.pop()

        avc3 = el.availableDataSources()
        cpx3 = el.dataSources(avc3)
        self.assertTrue(isinstance(avc3, list))

        for i in range(len(avc)):
            self.assertTrue(avc[i] in avc3)
            j = avc3.index(avc[i])
            self.assertEqual(cpx3[j], cpx[i])

        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision+4)
        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_mandatory_no_comp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()
        man = el.mandatoryComponents()
        self.assertTrue(isinstance(man, list))
        avc = el.availableComponents()

        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc

        self.assertEqual(el.setMandatoryComponents([name]), None)
        man2 = el.mandatoryComponents()
#        for cp in man:
#            self.assertTrue(cp in man2)

        #        self.assertTrue(name in man2)
        self.assertEqual(len(man),len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_mandatory_comp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()
        man = el.mandatoryComponents()
        self.assertTrue(isinstance(man, list))
        avc = el.availableComponents()

        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

#        print man
        self.assertEqual(el.setMandatoryComponents([name]), None)
        self.assertEqual(el.setMandatoryComponents([name]), None)
        man2 = el.mandatoryComponents()
        self.assertEqual(len(man)+1,len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(name in man2)

        self.assertEqual(el.unsetMandatoryComponents([name]), None)
        self.assertEqual(el.unsetMandatoryComponents([name]), None)

        man2 = el.mandatoryComponents()
        self.assertEqual(len(man),len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(not name in man2)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        man2 = el.mandatoryComponents()
        self.assertEqual(len(man),len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(not name in man2)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 4)
        self.assertEqual(el.close(), None)

    ##  component test
    # \brief It tests default settings
    def ttest_mandatory_comp2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = self.openConf()
        man = el.mandatoryComponents()
        self.assertTrue(isinstance(man, list))
        avc = el.availableComponents()

        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'

        name2 = name + '_2'
        while name2 in avc:
            name2 = name2 + '_2'
#        print avc

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)

#        print man
        self.assertEqual(el.setMandatoryComponents([name]), None)
        man2 = el.mandatoryComponents()
        self.assertEqual(len(man)+1,len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(name in man2)

        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)

#        print man
        self.assertEqual(el.setMandatoryComponents([name2]), None)
        man2 = el.mandatoryComponents()
        self.assertEqual(len(man)+2,len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(name in man2)
        self.assertTrue(name2 in man2)

        self.assertEqual(el.unsetMandatoryComponents([name]), None)

#        print man
        man2 = el.mandatoryComponents()
        self.assertEqual(len(man)+1,len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(name2 in man2)

        self.assertEqual(el.unsetMandatoryComponents([name2]), None)

        man2 = el.mandatoryComponents()
        self.assertEqual(len(man),len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(not name in man2)

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()

        man2 = el.mandatoryComponents()
        self.assertEqual(len(man),len(man2))
        for cp in man:
            self.assertTrue(cp in man2)

        self.assertTrue(not name in man2)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 8)
        self.assertEqual(el.close(), None)

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()

        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        xml = self.getXML(el)
        self.assertEqual(self.getXML(el), '')
        self.assertEqual(el.createConfiguration([]), None)
        xml = self.getXML(el)
        self.assertEqual(self.getXML(el), '')
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry' name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        name2 = "mcs_var_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry' name='$var.myentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><doc>$var(myentry=entry2)</doc></definition>"
        while name in avc:
            name = name + '_1'
        while name2 in avc:
            name2 = name2 + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)
        cpx2 = el.components([name2])
        self.assertEqual(cpx2[0], xml2)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type="NXentry"/></definition>')

        el.variables = '{}'
        self.assertEqual(el.createConfiguration([name, name2]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry2" type="NXentry"/> <doc>$var(myentry=entry2)</doc></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name, name2]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/> <doc>$var(myentry=entry2)</doc></definition>')

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()


    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='$var.entryType' name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type=""/></definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()


    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        name2 = "mcs_var_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='$var.entryType' name='$var.myentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition>" \
               "<doc>$var(myentry=entry2) $var(entryType=NXentry)</doc>" \
               "</definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        while name2 in avc:
            name2 = name2 + '_1'
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type=""/>'
            '</definition>')


        el.variables = '{}'
        self.assertEqual(el.createConfiguration([name, name2]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry2" type="NXentry"/>'
            ' <doc>$var(myentry=entry2) $var(entryType=NXentry)</doc>'
            '</definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2_cp_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        name2 = "mcs_var_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='$var.entryType' name='$var.myentry#\"12def34\"'/></definition>"
        xml2 = "<?xml version='1.0'?><definition>" \
               "<doc>$var(myentry=entry2) $var(entryType=NXentry)</doc>" \
               "</definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        while name2 in avc:
            name2 = name2 + '_1'
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type=""/>'
            '</definition>')


        el.variables = '{}'
        self.assertEqual(el.createConfiguration([name, name2]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry2" type="NXentry"/>'
            ' <doc>$var(myentry=entry2) $var(entryType=NXentry)</doc>'
            '</definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2_cp_default2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        name2 = "mcs_var_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='NXentry' name='entry'>" \
              "<group type='NXinstrument' name='instrument'> " \
              "<group type='NXdetector' name='$var.detector#\"mydetector\"'>" \
             "<group type='NXtransformations' name='transformations'/>" \
             "</group></group></group></definition>"
        xml2 = "<?xml version='1.0'?><definition>" \
               "<group type='NXentry' name='entry'>" \
               "<group type='NXinstrument' name='instrument'>" \
               "<group type='NXdetector' name='pilatus'>" \
               "<field type='NX_FLOAT64' name='data'/>" \
               "</group></group></group>" \
               "<doc>$var(detector=pilatus)</doc>" \
               "</definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        while name2 in avc:
            name2 = name2 + '_1'
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry" type="NXentry">'
            '  <group name="instrument" type="NXinstrument">'
            '       <group name="mydetector" type="NXdetector">'
            '    <group name="transformations" type="NXtransformations"/>'
            '   </group>  </group> </group></definition>')


        el.variables = '{}'
        self.assertEqual(el.createConfiguration([name, name2]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry" type="NXentry">'
            '  <group name="instrument" type="NXinstrument">'
            '       <group name="pilatus" type="NXdetector">'
            '    <group name="transformations" type="NXtransformations"/>'
            '    <field name="data" type="NX_FLOAT64"/>'
            '   </group>  </group> </group> '
            '<doc>$var(detector=pilatus)</doc></definition>'
        )

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='NXentry' name='$var.myentry#\"12def34\"'/>" \
              "</definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            ' <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var_default_q(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry' name='$var.myentry#\&quot;12def34\&quot;'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()
    def ttest_createConf_default_2_var_default_q2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry' name='$var.myentry#&quot;12def34&quot;'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    def ttest_createConf_default_2_var_defaul_t2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = '<?xml version=\'1.0\'?><definition><group type="NXentry" name="$var.myentry#\"12def34\""/></definition>'
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    def ttest_createConf_default_2_var_defaul_t2q(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = '<?xml version=\'1.0\'?><definition><group type="NXentry" name="$var.myentry#\&quot;12def34\&quot;"/></definition>'
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    def ttest_createConf_default_2_var_defaul_t2q2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = '<?xml version=\'1.0\'?><definition><group type="NXentry" name="$var.myentry#&quot;12def34&quot;"/></definition>'
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='$var.entryType#\'myty\'' name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type="myty"/></definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var_default2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = '<?xml version=\'1.0\'?><definition><group type=\'NXentry\' name=\'$var.myentry#\"12def34\"\'/></definition>'
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)
        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="12def34" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    # \brief It tests XMLConfigurator
    def ttest_createConf_default_2_var2_default2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type=\"$var.entryType#'myty'\" name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="" type="myty"/></definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        self.assertEqual(el.createConfiguration([name]), None)

        xml = self.getXML(el)
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition> <group name="entry1" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_def(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<group type='NXentry'/>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.myAssertRaise(UndefinedTagError,el.createConfiguration,[name])

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = ["mcs_test_component"]
        xml = ["<definition/>", "<definition><group type='NXentry'/></definition>"]
        name.append(name[0] +'_2')
        while name[0] in avc:
            name[0] = name[0] + '_1'
        while name[1] in avc:
            name[1] = name[1] + '_2'
#        print avc
        self.setXML(el, xml[0])
        self.assertEqual(el.storeComponent(name[0]), None)
        self.__cmps.append(name[0])

        self.setXML(el, xml[1])
        self.assertEqual(el.storeComponent(name[1]), None)
        self.__cmps.append(name[1])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"),
                         '<?xml version="1.0" ?><definition> <group type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name[1]), None)
        self.__cmps.pop()

        self.assertEqual(el.deleteComponent(name[0]), None)
        self.__cmps.pop()

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_5(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = [ "<definition><group type='NXentry'/></definition>"]*5
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <group type="NXentry"/></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 10)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry2"/> <group type="NXentry"/></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <group type="NXentry2"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])
        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<group/>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(UndefinedTagError,el.createConfiguration, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_error_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<group/>", "<definition><group type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(UndefinedTagError,el.createConfiguration, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_field_3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field type='field'/></group></definition>"]*3
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <group type="NXentry">  <field type="field"/> </group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_field(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man
        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field name='field1'/></group></definition>", "<definition><group type='NXentry2'/><field name='field1'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition> <group type="NXentry2"/> <field name="field1"/> <group type="NXentry">  <field name="field1"/> </group></definition>') |
                        (gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition> <group type="NXentry">  <field name="field1"/> </group> <group type="NXentry2"/> <field name="field1"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <group name="entry" type="NXentry2"/></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry'/></definition>", "<definition><group name='entry' type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition> <group name="entry" type="NXentry"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_4(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry2'/></definition>", "<definition><group name='entry' type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><")== '<?xml version="1.0" ?><definition> <group name="entry" type="NXentry"/> <group name="entry2"/></definition>') |
                        (gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition> <group name="entry2"/> <group name="entry" type="NXentry"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_field_4(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field type='field'/></group></definition>"]*15
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition> <group type="NXentry">  <field type="field"/> </group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 30)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_field_5(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry' type='NXentry'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition> <group name="entry" type="NXentry">  <field type="field"/> </group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_field_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='$var.entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='$var.entry' type='NXentry'><field type='field'>$var.value</field></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.variables = '{"entry":"entry", "value":"myvalue", "some":"ble"}'
        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("> ", ">").replace(">  ", ">").replace(">   ", ">").replace(" <", "<").replace("  <", "<").replace("   <", "<").replace("?>\n<", "?><").replace(" <", "<"),
                         '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field type="field">myvalue</field></group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_field_name_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry' type='NXentry2'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_single_name(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry2' type='NXentry2'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.assertEqual(el.createConfiguration(name), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group name="entry2" type="NXentry2">  <field type="field"/> </group> <group name="entry" type="NXentry">  <field type="field"/> </group></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group name="entry" type="NXentry">  <field type="field"/> </group> <group name="entry2" type="NXentry2">  <field type="field"/> </group></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + np*2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_single_name_2_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        mr = Merger()
        for sg in mr.singles:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            revision = long(el.version.split('.')[-1])

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' type='NXentry'><%s name='field2'/></group></definition>" % sg,"<definition><group name='entry2' type='NXentry2'><%s name='field'/></group></definition>" % sg]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

            self.assertEqual(long(el.version.split('.')[-1]), revision + 2*np)

            el.setMandatoryComponents(man)
            el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_uniqueText_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        mr = Merger()
        for ut in mr.uniqueText:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            revision = long(el.version.split('.')[-1])

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' type='NXentry'><%s type='field'>My text </%s></group></definition>" %(ut ,ut),"<definition><group  name='entry' type='NXentry'><%s type='field'>My text 2 </%s></group></definition>" %(ut ,ut)]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2*np)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_datasource(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = self.children
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><datasource type='TANGO'><%s/></datasource></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition> <field name="entry">  <datasource type="TANGO">   <%s/>  </datasource> </field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_datasource_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  self.children:
                    uts.append(w)

        uts = set(uts)

        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><datasource type='TANGO'><%s/></datasource></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            el.createConfiguration(name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_attribute(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['attribute']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><attribute type='TANGO'><%s/></attribute></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition> <field name="entry">  <attribute type="TANGO">   <%s/>  </attribute> </field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_attribute_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["attribute"]:
                    uts.append(w)
        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><attribute type='TANGO'><%s/></attribute></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_definition(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['definition']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><%s  name='entry' /></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition> <%s name="entry"/></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_definition_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["definition"]:
                    uts.append(w)

        uts = set(uts)

        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><%s  name='entry' /></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_dimensions(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['dimensions']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><dimensions type='TANGO'><%s/></dimensions></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <field name="entry">  <dimensions type="TANGO">   <%s/>  </dimensions> </field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_dimensions_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["dimensions"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><dimensions type='TANGO'><%s/></dimensions></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_field(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['field']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><%s/></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <field name="entry">  <%s/> </field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_field_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["field"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><%s/></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['group']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' ><%s/></group></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition> <group name="entry">  <%s/> </group></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_group_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["group"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' ><%s/></group></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_link(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['link']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><link  name='entry' ><%s/></link></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.assertEqual(el.createConfiguration(name), None)
            gxml = self.getXML(el)
            self.assertEqual(gxml.replace("?>\n<", "?><"),
                             '<?xml version="1.0" ?><definition> <link name="entry">  <%s/> </link></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_children_link_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["link"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            revision = long(el.version.split('.')[-1])

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><link  name='entry' ><%s/></link></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.createConfiguration, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_mandatory(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.setMandatoryComponents([name[0]])
        self.assertEqual(el.mandatoryComponents(),[name[0]])

        self.assertEqual(el.createConfiguration([name[1]]), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry2"/> <group type="NXentry"/></definition>') |
                         (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <group type="NXentry2"/></definition>'))

        el.unsetMandatoryComponents([name[0]])
        self.assertEqual(el.mandatoryComponents(),[])

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConf_group_group_group_mandatory(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>",
               "<definition><group type='NXentry2'/></definition>",
               "<definition><group type='NXentry3'/></definition>"
               ]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.setMandatoryComponents([name[0], name[1]])
        self.assertEqual(el.mandatoryComponents().sort(),[name[0], name[1]].sort())

        self.assertEqual(el.createConfiguration([name[2]]), None)
        gxml = self.getXML(el)

        self.assertTrue(
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry2"/> <group type="NXentry3"/> <group type="NXentry"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry3"/> <group type="NXentry2"/> <group type="NXentry"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry3"/> <group type="NXentry"/> <group type="NXentry2"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry2"/> <group type="NXentry"/> <group type="NXentry3"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry"/> <group type="NXentry2"/> <group type="NXentry3"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry"/> <group type="NXentry3"/> <group type="NXentry2"/></definition>')
        )

        el.unsetMandatoryComponents([name[1]])

        self.assertEqual(el.mandatoryComponents(),[name[0]])

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(el.mandatoryComponents(),[])

        self.assertEqual(long(el.version.split('.')[-1]), revision + 9)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_default(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()

        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        xml = self.getXML(el)
        self.assertEqual(self.getXML(el), '')
        xml  = el.merge([])
        self.assertEqual(self.getXML(el), '')
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_default_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='NXentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        xml = el.merge([name])
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition><group type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_default_2_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='NXentry' name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        xml = el.merge([name])
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            '<group name="$var.myentry" type="NXentry"/></definition>')

        el.variables = '{"myentry":"entry1"}'
        xml = el.merge([name])

        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            '<group name="$var.myentry" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_default_2_var_cp(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        name2 = "mcs_var_component"
        xml = "<?xml version='1.0'?><definition>" \
              "<group type='NXentry' name='$var.myentry'/></definition>"
        xml2 = "<?xml version='1.0'?><definition><doc>$var(myentry=entry2)</doc></definition>"
        while name in avc:
            name = name + '_1'
        while name2 in avc:
            name2 = name2 + '_1'
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        self.setXML(el, xml2)
        self.assertEqual(el.storeComponent(name2), None)
        self.__cmps.append(name2)
        avc2 = el.availableComponents()
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)
        cpx2 = el.components([name2])
        self.assertEqual(cpx2[0], xml2)

        xml = el.merge([name])
        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            '<group name="$var.myentry" type="NXentry"/></definition>')

        xml = el.merge([name, name2])

        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            '<group name="$var.myentry" type="NXentry"/>'
            '<doc>$var(myentry=entry2)</doc></definition>')
        el.variables = '{"myentry":"entry1"}'
        xml = el.merge([name])

        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition>'
            '<group name="$var.myentry" type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name2), None)
        self.__cmps.pop()
        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    # \brief It tests XMLConfigurator
    def ttest_merge_default_2_var2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<?xml version='1.0'?><definition><group type='$var.entryType' name='$var.myentry'/></definition>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        xml = el.merge([name])

        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition><group name="$var.myentry" type="$var.entryType"/></definition>')
        el.variables = '{"myentry":"entry1", "entryType":"NXentry"}'
        xml = el.merge([name])

        self.assertEqual(
            xml.replace("?>\n<", "?><"),
            '<?xml version="1.0" ?><definition><group name="$var.myentry" type="$var.entryType"/></definition>')

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_def(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = "mcs_test_component"
        xml = "<group type='NXentry'/>"
        while name in avc:
            name = name + '_1'
#        print avc
        self.setXML(el, xml)
        self.assertEqual(el.storeComponent(name), None)
        self.__cmps.append(name)
        avc2 = el.availableComponents()
#        print avc2
        self.assertTrue(isinstance(avc2, list))
        for cp in avc:
            self.assertTrue(cp in avc2)

        self.assertTrue(name in avc2)

        cpx = el.components([name])
        self.assertEqual(cpx[0], xml)

        self.myAssertRaise(UndefinedTagError,el.merge,[name])

        self.assertEqual(el.deleteComponent(name), None)
        self.__cmps.pop()

        avc3 = el.availableComponents()
        self.assertTrue(isinstance(avc3, list))
        for cp in avc:
            self.assertTrue(cp in avc3)
        self.assertTrue(name not in avc3)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        self.assertTrue(isinstance(avc, list))
        name = ["mcs_test_component"]
        xml = ["<definition/>", "<definition><group type='NXentry'/></definition>"]
        name.append(name[0] +'_2')
        while name[0] in avc:
            name[0] = name[0] + '_1'
        while name[1] in avc:
            name[1] = name[1] + '_2'
#        print avc
        self.setXML(el, xml[0])
        self.assertEqual(el.storeComponent(name[0]), None)
        self.__cmps.append(name[0])

        self.setXML(el, xml[1])
        self.assertEqual(el.storeComponent(name[1]), None)
        self.__cmps.append(name[1])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"),
                         '<?xml version="1.0" ?><definition><group type="NXentry"/></definition>')

        self.assertEqual(el.deleteComponent(name[1]), None)
        self.__cmps.pop()

        self.assertEqual(el.deleteComponent(name[0]), None)
        self.__cmps.pop()

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_5(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = [ "<definition><group type='NXentry'/></definition>"]*5
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><group type="NXentry"/></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + np*2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry2"/><group type="NXentry"/></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><group type="NXentry2"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + np*2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<group/>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(UndefinedTagError,el.merge, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_error_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<group/>", "<definition><group type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(UndefinedTagError,el.merge, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_field_3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field type='field'/></group></definition>"]*3
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><group type="NXentry"><field type="field"/></group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_field(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field name='field1'/></group></definition>", "<definition><group type='NXentry2'/><field name='field1'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry2"/><field name="field1"/><group type="NXentry"><field name="field1"/></group></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"><field name="field1"/></group><group type="NXentry2"/><field name="field1"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><group name="entry" type="NXentry2"/></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_3(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry'/></definition>", "<definition><group name='entry' type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><group name="entry" type="NXentry"/></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_4(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group name='entry2'/></definition>", "<definition><group name='entry' type='NXentry'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"/><group name="entry2"/></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group name="entry2"/><group name="entry" type="NXentry"/></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_field_4(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'><field type='field'/></group></definition>"]*15
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition><group type="NXentry"><field type="field"/></group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 30)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_field_5(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry' type='NXentry'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field type="field"/></group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_field_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='$var.entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='$var.entry' type='NXentry'><field type='field'>$var.value</field></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.variables = '{"entry":"entry", "value":"myvalue", "some":"ble"}'
        gxml = el.merge(name)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition><group name="$var.entry" type="NXentry"><field type="field">$var.value</field></group></definition>')

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_field_name_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man
        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry' type='NXentry2'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        self.myAssertRaise(IncompatibleNodeError,el.merge, name)

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_single_name(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man
        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group  name='entry' type='NXentry'><field type='field'/></group></definition>", "<definition><group name='entry2' type='NXentry2'><field type='field'/></group></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        gxml = el.merge(name)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group name="entry2" type="NXentry2"><field type="field"/></group><group name="entry" type="NXentry"><field type="field"/></group></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field type="field"/></group><group name="entry2" type="NXentry2"><field type="field"/></group></definition>'))

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_single_name_2_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        mr = Merger()
        for sg in mr.singles:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' type='NXentry'><%s name='field2'/></group></definition>" % sg,"<definition><group name='entry2' type='NXentry2'><%s name='field'/></group></definition>" % sg]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 4)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_uniqueText_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        mr = Merger()
        for ut in mr.uniqueText:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' type='NXentry'><%s type='field'>My text </%s></group></definition>" %(ut ,ut),"<definition><group  name='entry' type='NXentry'><%s type='field'>My text 2 </%s></group></definition>" %(ut ,ut)]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 4)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_datasource(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = self.children
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><datasource type='TANGO'><%s/></datasource></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition><field name="entry"><datasource type="TANGO"><%s/></datasource></field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_datasource_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  self.children:
                    uts.append(w)

        uts = set(uts)

        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><datasource type='TANGO'><%s/></datasource></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            el.merge(name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_attribute(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['attribute']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><attribute type='TANGO'><%s/></attribute></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition><field name="entry"><attribute type="TANGO"><%s/></attribute></field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_attribute_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["attribute"]:
                    uts.append(w)
        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><attribute type='TANGO'><%s/></attribute></field></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_definition(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['definition']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><%s  name='entry' /></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),  '<?xml version="1.0" ?><definition><%s name="entry"/></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_definition_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["definition"]:
                    uts.append(w)

        uts = set(uts)

        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><%s  name='entry' /></definition>" % ut ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_dimensions(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['dimensions']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><dimensions type='TANGO'><%s/></dimensions></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><field name="entry"><dimensions type="TANGO"><%s/></dimensions></field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision+2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_dimensions_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["dimensions"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><dimensions type='TANGO'><%s/></dimensions></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_field(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['field']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><%s/></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><field name="entry"><%s/></field></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_field_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["field"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><field  name='entry' ><%s/></field></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision +2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_group(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['group']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' ><%s/></group></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),'<?xml version="1.0" ?><definition><group name="entry"><%s/></group></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_group_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["group"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><group  name='entry' ><%s/></group></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_link(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = el.children['link']
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><link  name='entry' ><%s/></link></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            gxml = el.merge(name)
            self.assertEqual(gxml.replace("?>\n<", "?><"),
                             '<?xml version="1.0" ?><definition><link name="entry"><%s/></link></definition>' % (ut))

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        el.setMandatoryComponents(man)
        self.assertEqual(long(el.version.split('.')[-1]), self.revision + 2)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_children_link_error(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)
        el = Merger()
        uts = []
        for k in el.children:
            for w in el.children[k]:
                if w not in  el.children["link"]:
                    uts.append(w)

        uts = set(uts)
        for ut in uts:

            el = self.openConf()
            man = el.mandatoryComponents()
            el.unsetMandatoryComponents(man)
            self.__man += man

            revision = long(el.version.split('.')[-1])

            avc = el.availableComponents()

            oname = "mcs_test_component"
            self.assertTrue(isinstance(avc, list))
            xml = ["<definition><link  name='entry' ><%s/></link></definition>" % ut  ]
            np = len(xml)
            name = []
            for i in range(np):

                name.append(oname +'_%s' % i)
                while name[i] in avc:
                    name[i] = name[i] + '_%s' %i
#        print avc

            for i in range(np):
                self.setXML(el, xml[i])
                self.assertEqual(el.storeComponent(name[i]), None)
                self.__cmps.append(name[i])

            self.myAssertRaise(IncompatibleNodeError,el.merge, name)

            for i in range(np):
                self.assertEqual(el.deleteComponent(name[i]), None)
                self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 2)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_mandatory(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>", "<definition><group type='NXentry2'/></definition>"]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.setMandatoryComponents([name[0]])
        self.assertEqual(el.mandatoryComponents(),[name[0]])

        gxml = el.merge([name[1]])
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry2"/><group type="NXentry"/></definition>') |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><group type="NXentry2"/></definition>'))

        el.unsetMandatoryComponents([name[0]])
        self.assertEqual(el.mandatoryComponents(),[])

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_group_group_group_mandatory(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ["<definition><group type='NXentry'/></definition>",
               "<definition><group type='NXentry2'/></definition>",
               "<definition><group type='NXentry3'/></definition>"
               ]
        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.setMandatoryComponents([name[0], name[1]])
        self.assertEqual(el.mandatoryComponents().sort(),[name[0], name[1]].sort())

        gxml = el.merge([name[2]])

        self.assertTrue(
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry2"/><group type="NXentry3"/><group type="NXentry"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry3"/><group type="NXentry2"/><group type="NXentry"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry3"/><group type="NXentry"/><group type="NXentry2"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry2"/><group type="NXentry"/><group type="NXentry3"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry"/><group type="NXentry2"/><group type="NXentry3"/></definition>') |
            (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry"/><group type="NXentry3"/><group type="NXentry2"/></definition>')
        )

        el.unsetMandatoryComponents([name[1]])

        self.assertEqual(el.mandatoryComponents(),[name[0]])

        for i in range(np):
            self.assertEqual(el.deleteComponent(name[i]), None)
            self.__cmps.pop(0)

        self.assertEqual(el.mandatoryComponents(),[])

        self.assertEqual(long(el.version.split('.')[-1]), revision + 9)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentVariables(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        vrs =  ["eid", "myvar1", "var2", "mvar3"]

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry" name="entry$var.%s"/><field name="field1">some</field></definition>'
               % (vrs[0]),
               '<definition><group type="NXentry"/><field name="field2">$var.%s</field></definition>'
               % (vrs[1]),
               '<definition><group type="NXentry"/><field name="field3">$var.%s</field><field name="field4">$var.%s</field></definition>'
               % (vrs[2], vrs[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentVariables(cs)
            cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([vrs[0],vrs[2],vrs[3]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +3)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsVariables(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        vrs =  ["entry_id", "myvar1", "var2", "mvar3"]

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry" name="entry$var.%s"/><field name="field1">some</field></definition>'
               % (vrs[0]),
               '<definition><group type="NXentry"/><field name="field2">$var.%s</field></definition>'
               % (vrs[1]),
               '<definition><group type="NXentry"/><field name="field3">$var.%s</field><field name="field4">$var.%s</field></definition>'
               % (vrs[2], vrs[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsVariables(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([vrs[0],vrs[2],vrs[3]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +3)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_dependentComponents(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        oname = "mcs_test_component"

        avc = el.availableComponents()

        vrs =  ["eid", "myvar1", "var2", "mvar3"]

        np = 6
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field4"></field><field name="field4"></field>$components.%s$components.%s</definition>'
               % (name[1], name[2]),
               '<definition>$components.%s$components.%s<group type="NXentry"/><field name="field5"></field><field name="field4"></field></definition>'
               % (name[2], name[3]),
               '<definition><group type="NXentry" name="entry$components.%s"/><field name="field">some</field></definition>'
               % (name[4]),
               '<definition><group type="NXentry"/><field name="field1">$components.%s</field></definition>'
               % (name[5]),
               '<definition><group type="NXentry"/><field name="field2"></field><field name="field4"></field></definition>' ,
               '<definition><group type="NXentry"/><field name="field3"></field><field name="field4"></field></definition>'
               ]

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        arr =[
            [[],[]],
            [[0],[0,1,2,3,4,5]],
            [[1],[1,2,3,4,5]],
            [[2],[2,4]],
            [[3],[3,5]],
            [[4],[4]],
            [[5],[5]],
            [[0,1],[0,1,2,3,4,5]],
            [[0,2],[0,1,2,3,4,5]],
            [[0,3],[0,1,2,3,4,5]],
            [[0,4],[0,1,2,3,4,5]],
            [[0,5],[0,1,2,3,4,5]],
            [[1,2],[1,2,3,4,5]],
            [[1,3],[1,2,3,4,5]],
            [[1,4],[1,2,3,4,5]],
            [[1,5],[1,2,3,4,5]],
            [[2,3],[2,3,4,5]],
            [[2,4],[2,4]],
            [[2,5],[2,4,5]],
            [[3,4],[3,4,5]],
            [[3,5],[3,5]],
            [[4,5],[4,5]],
            [[0,2,1],[0,1,2,3,4,5]],
            [[0,3,1],[0,1,2,3,4,5]],
            [[0,4,1],[0,1,2,3,4,5]],
            [[0,5,1],[0,1,2,3,4,5]],
            [[0,3,2],[0,1,2,3,4,5]],
            [[0,4,2],[0,1,2,3,4,5]],
            [[0,5,2],[0,1,2,3,4,5]],
            [[0,4,3],[0,1,2,3,4,5]],
            [[0,5,3],[0,1,2,3,4,5]],
            [[0,5,4],[0,1,2,3,4,5]],
            [[1,3,2],[1,2,3,4,5]],
            [[1,4,2],[1,2,3,4,5]],
            [[1,5,2],[1,2,3,4,5]],
            [[1,4,3],[1,2,3,4,5]],
            [[1,5,3],[1,2,3,4,5]],
            [[1,5,4],[1,2,3,4,5]],
            [[2,4,3],[2,3,4,5]],
            [[2,5,3],[2,3,4,5]],
            [[2,5,4],[2,4,5]],
            [[3,4,5],[3,4,5]],
            [[0,1,2,3],[0,1,2,3,4,5]],
            [[0,1,2,4],[0,1,2,3,4,5]],
            [[0,1,2,5],[0,1,2,3,4,5]],
            [[0,1,3,4],[0,1,2,3,4,5]],
            [[0,1,3,5],[0,1,2,3,4,5]],
            [[0,1,4,5],[0,1,2,3,4,5]],
            [[1,2,3,4],[1,2,3,4,5]],
            [[1,2,3,5],[1,2,3,4,5]],
            [[1,2,4,5],[1,2,3,4,5]],
            [[1,3,4,5],[1,2,3,4,5]],
            [[2,3,4,5],[2,3,4,5]],
            [[0,1,2,3,4],[0,1,2,3,4,5]],
            [[0,1,2,3,5],[0,1,2,3,4,5]],
            [[0,1,2,4,5],[0,1,2,3,4,5]],
            [[0,1,3,4,5],[0,1,2,3,4,5]],
            [[0,1,3,4,5],[0,1,2,3,4,5]],
            [[0,2,3,4,5],[0,1,2,3,4,5]],
            [[1,2,3,4,5],[1,2,3,4,5]],
            [[0,1,2,3,4,5],[0,1,2,3,4,5]],
            ]

        for ar in arr:

            css = [name[i]  for  i in ar[0]]
            cmps = []
            mdss = el.dependentComponents(css)
            self.assertEqual(sorted(mdss), sorted([name[i]  for  i in ar[1]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_dependentComponents_man(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        oname = "mcs_test_component"

        avc = el.availableComponents()

        vrs =  ["eid", "myvar1", "var2", "mvar3"]

        np = 6
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field4"></field><field name="field4"></field>$components.%s$components.%s</definition>'
               % (name[1], name[2]),
               '<definition>$components.%s$components.%s<group type="NXentry"/><field name="field5"></field><field name="field4"></field></definition>'
               % (name[2], name[3]),
               '<definition><group type="NXentry" name="entry$components.%s"/><field name="field">some</field></definition>'
               % (name[4]),
               '<definition><group type="NXentry"/><field name="field1">$components.%s</field></definition>'
               % (name[5]),
               '<definition><group type="NXentry"/><field name="field2"></field><field name="field4"></field></definition>' ,
               '<definition><group type="NXentry"/><field name="field3"></field><field name="field4"></field></definition>'
               ]

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        arr =[
            [[],[0],[]],
            [[0],[0],[0,1,2,3,4,5]],
            [[1],[0],[1,2,3,4,5]],
            [[2],[2],[2,4]],
            [[3],[0],[3,5]],
            [[4],[1,2],[4]],
            [[5],[3],[5]],
            [[0,1],[0],[0,1,2,3,4,5]],
            [[0,2],[4],[0,1,2,3,4,5]],
            [[0,3],[4],[0,1,2,3,4,5]],
            [[0,4],[0],[0,1,2,3,4,5]],
            [[0,5],[2,5],[0,1,2,3,4,5]],
            [[1,2],[0],[1,2,3,4,5]],
            [[1,3],[2],[1,2,3,4,5]],
            [[1,4],[0],[1,2,3,4,5]],
            [[1,5],[3],[1,2,3,4,5]],
            [[2,3],[4],[2,3,4,5]],
            [[2,4],[0],[2,4]],
            [[2,5],[3],[2,4,5]],
            [[3,4],[0],[3,4,5]],
            [[3,5],[1],[3,5]],
            [[4,5],[0],[4,5]],
            [[0,2,1],[1],[0,1,2,3,4,5]],
            [[0,3,1],[0],[0,1,2,3,4,5]],
            [[0,4,1],[3],[0,1,2,3,4,5]],
            [[0,5,1],[4],[0,1,2,3,4,5]],
            [[0,3,2],[5],[0,1,2,3,4,5]],
            [[0,4,2],[0],[0,1,2,3,4,5]],
            [[0,5,2],[3],[0,1,2,3,4,5]],
            [[0,4,3],[4],[0,1,2,3,4,5]],
            [[0,5,3],[1],[0,1,2,3,4,5]],
            [[0,5,4],[2],[0,1,2,3,4,5]],
            [[1,3,2],[3],[1,2,3,4,5]],
            [[1,4,2],[0],[1,2,3,4,5]],
            [[1,5,2],[4],[1,2,3,4,5]],
            [[1,4,3],[2],[1,2,3,4,5]],
            [[1,5,3],[3],[1,2,3,4,5]],
            [[1,5,4],[1],[1,2,3,4,5]],
            [[2,4,3],[2],[2,3,4,5]],
            [[2,5,3],[3],[2,3,4,5]],
            [[2,5,4],[4],[2,4,5]],
            [[3,4,5],[0,1,2,3,4,5],[3,4,5]],
            [[0,1,2,3],[1],[0,1,2,3,4,5]],
            [[0,1,2,4],[0],[0,1,2,3,4,5]],
            [[0,1,2,5],[1],[0,1,2,3,4,5]],
            [[0,1,3,4],[2],[0,1,2,3,4,5]],
            [[0,1,3,5],[3],[0,1,2,3,4,5]],
            [[0,1,4,5],[4],[0,1,2,3,4,5]],
            [[1,2,3,4],[5],[1,2,3,4,5]],
            [[1,2,3,5],[1],[1,2,3,4,5]],
            [[1,2,4,5],[2],[1,2,3,4,5]],
            [[1,3,4,5],[3],[1,2,3,4,5]],
            [[2,3,4,5],[4],[2,3,4,5]],
            [[0,1,2,3,4],[1],[0,1,2,3,4,5]],
            [[0,1,2,3,5],[2],[0,1,2,3,4,5]],
            [[0,1,2,4,5],[3],[0,1,2,3,4,5]],
            [[0,1,3,4,5],[0],[0,1,2,3,4,5]],
            [[0,1,3,4,5],[2,1,2,3,4],[0,1,2,3,4,5]],
            [[0,2,3,4,5],[3],[0,1,2,3,4,5]],
            [[1,2,3,4,5],[3],[1,2,3,4,5]],
            [[0,1,2,3,4,5],[2],[0,1,2,3,4,5]],
            ]

        for ar in arr:
            css = [name[i]  for  i in ar[0]]
            cmps = []
            el.setMandatoryComponents([name[i]  for  i in ar[1]])
            mdss = el.dependentComponents(css)
            el.unsetMandatoryComponents([name[i]  for  i in ar[1]])
            self.assertEqual(sorted(mdss), sorted([name[i]  for  i in ar[2]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +148)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentDataSources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el,xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % (xds[0] % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % (xds[1] % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,xds[3] % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0],dsname[2],dsname[3]])

        self.assertEqual(long(el.version.split('.')[-1]), revision +7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentDataSources_external(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0],dsname[2],dsname[3]])

        self.assertEqual(long(el.version.split('.')[-1]), revision+7)
        el.setMandatoryComponents(man)
        el.close()



    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_setComponentDataSources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        xml2 = [
            '<definition><group type="NXentry"/><field name="field1">%s'
            '</field></definition>',
            '<definition><group type="NXentry"/><field name="field2">%s'
            '</field></definition>',
            '<definition><group type="NXentry"/><field name="field3">%s'
            '</field><field name="field4">%s</field></definition>'
        ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0], dsname[2], dsname[3]])

        el.setComponentDataSources(
            json.dumps({name[0]: {dsname[0]: dsname[1]}})
        )
        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] in avcp2)
        self.__cmps.append(tname[0])

        mdss = el.componentDataSources(tname[0])
        self.assertEqual(set(mdss), set([dsname[0]]))
        mdss = el.componentDataSources(name[0])
        self.assertEqual(set(mdss), set([dsname[1]]))
        self.assertEqual(
            el.components([name[0]])[0],
            xml2[0] % ("$datasources.%s" % dsname[1]))
        self.assertEqual(el.components([tname[0]])[0], xml[0])

        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(
            set(cmps),
            set([dsname[0], dsname[1], dsname[2], dsname[3]]))


        el.setComponentDataSources(
            json.dumps({name[0]: {dsname[0]: dsname[2]},
                        name[1]: {dsname[1]: dsname[0]}})
        )
        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] in avcp2)
        self.assertTrue(tname[1] in avcp2)
        self.__cmps.append(tname[1])

        mdss = el.componentDataSources(tname[0])
        self.assertEqual(set(mdss), set([dsname[0]]))
        mdss = el.componentDataSources(name[0])
        self.assertEqual(set(mdss), set([dsname[2]]))
        self.assertEqual(
            el.components([name[0]])[0],
            xml2[0] % ("$datasources.%s" % dsname[2]))
        self.assertEqual(el.components([tname[0]])[0], xml[0])

        mdss = el.componentDataSources(tname[1])
        self.assertEqual(set(mdss), set([dsname[1]]))
        mdss = el.componentDataSources(name[1])
        self.assertEqual(set(mdss), set([dsname[0]]))
        self.assertEqual(
            el.components([name[1]])[0],
            xml2[1] % ("$datasources.%s" % dsname[0]))
        self.assertEqual(el.components([tname[1]])[0], xml[1])

        self.assertEqual(long(el.version.split('.')[-1]), revision+12)
        el.setMandatoryComponents(man)
        el.close()



    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_setComponentDataSources_postrun(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        xml2 = [
            '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">%s'
            '</field></definition>',
            '<definition><group type="NXentry"/><field name="field2">%s'
            '</field></definition>',
            '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3">%s'
            '</field><field name="field4">%s</field></definition>'
        ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0], dsname[2], dsname[3]])

        el.setComponentDataSources(
            json.dumps({name[0]: {dsname[0]: ""}})
        )
        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] in avcp2)
        self.__cmps.append(tname[0])

        mdss = el.componentDataSources(tname[0])
        self.assertEqual(set(mdss), set([dsname[0]]))
        mdss = el.componentDataSources(name[0])
        self.assertEqual(set(mdss), set())
        self.assertEqual(
            el.components([name[0]])[0],
            xml2[0] % (""))
        self.assertEqual(el.components([tname[0]])[0], xml[0])

        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(
            set(cmps),
            set([dsname[0], dsname[2], dsname[3]]))


        el.setComponentDataSources(
            json.dumps({name[0]: {dsname[0]: ""},
                        name[1]: {dsname[1]: dsname[0]}})
        )
        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] in avcp2)
        self.assertTrue(tname[1] in avcp2)
        self.__cmps.append(tname[1])

        mdss = el.componentDataSources(tname[0])
        self.assertEqual(set(mdss), set([dsname[0]]))
        mdss = el.componentDataSources(name[0])
        self.assertEqual(set(mdss), set())
        self.assertEqual(
            el.components([name[0]])[0],
            xml2[0] % (""))
        self.assertEqual(el.components([tname[0]])[0], xml[0])

        mdss = el.componentDataSources(tname[1])
        self.assertEqual(set(mdss), set([dsname[1]]))
        mdss = el.componentDataSources(name[1])
        self.assertEqual(set(mdss), set([dsname[0]]))
        self.assertEqual(
            el.components([name[1]])[0],
            xml2[1] % ("$datasources.%s" % dsname[0]))
        self.assertEqual(el.components([tname[1]])[0], xml[1])

        self.assertEqual(long(el.version.split('.')[-1]), revision+11)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_setComponentDataSources_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        xml2 = [
            '<definition><group type="NXentry"/><field name="field1">%s'
            '</field></definition>',
            '<definition><group type="NXentry"/><field name="field2">%s'
            '</field></definition>',
            '<definition><group type="NXentry"/><field name="field3">%s'
            '</field><field name="field4">%s</field></definition>'
        ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0], dsname[2], dsname[3]])

        el.setComponentDataSources(
            json.dumps({name[2]: {dsname[2]: dsname[3],
                                  dsname[3]: dsname[1]},
                        name[1]: {dsname[1]: dsname[2]}})
        )
        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] not in avcp2)
        self.assertTrue(tname[1] in avcp2)
        self.assertTrue(tname[2] in avcp2)
        self.__cmps.append(tname[1])
        self.__cmps.append(tname[2])

        mdss = el.componentDataSources(tname[2])
        self.assertEqual(set(mdss), set([dsname[2], dsname[3]]))
        mdss = el.componentDataSources(name[2])
        self.assertEqual(set(mdss), set([dsname[3], dsname[1]]))
        self.assertEqual(
            el.components([name[2]])[0],
            xml2[2] % ("$datasources.%s" % dsname[3], "$datasources.%s" % dsname[1]))
        self.assertEqual(el.components([tname[2]])[0], xml[2])

        mdss = el.componentDataSources(tname[1])
        self.assertEqual(set(mdss), set([dsname[1]]))
        mdss = el.componentDataSources(name[1])
        self.assertEqual(set(mdss), set([dsname[2]]))
        self.assertEqual(
            el.components([name[1]])[0],
            xml2[1] % ("$datasources.%s" % dsname[2]))
        self.assertEqual(el.components([tname[1]])[0], xml[1])


        el.setComponentDataSources(
            json.dumps({name[2]: {}})
        )

        avcp2 = el.availableComponents()
        tname = ["__template__" + nm for nm in name]
        self.assertTrue(tname[0] not in avcp2)
        self.assertTrue(tname[1] in avcp2)
        self.assertTrue(tname[2] in avcp2)
        self.__cmps.append(tname[1])
        self.__cmps.append(tname[2])

        mdss = el.componentDataSources(tname[2])
        self.assertEqual(set(mdss), set([dsname[2], dsname[3]]))
        mdss = el.componentDataSources(name[2])
        self.assertEqual(set(mdss), set([dsname[2], dsname[3]]))
        self.assertEqual(el.components([tname[2]])[0], xml[2])
        self.assertEqual(el.components([name[2]])[0], xml[2])

        mdss = el.componentDataSources(tname[1])
        self.assertEqual(set(mdss), set([dsname[1]]))
        mdss = el.componentDataSources(name[1])
        self.assertEqual(set(mdss), set([dsname[2]]))
        self.assertEqual(
            el.components([name[1]])[0],
            xml2[1] % ("$datasources.%s" % dsname[2]))
        self.assertEqual(el.components([tname[1]])[0], xml[1])

        self.assertEqual(long(el.version.split('.')[-1]), revision+12)
        el.setMandatoryComponents(man)
        el.close()


    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentDataSources_external_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'
            print "AVDS", avds
            print "WW ", rename, dsname[0], dsname[1]

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[1],dsname[0]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision+5)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentDataSources_external_2_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3"><datasource>%s%s</datasource></field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            cmps.extend(mdss)
        self.assertEqual(set(cmps),set([dsname[0], '__unnamed__0', dsname[1]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision+5)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentDataSources_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % (xds[0] % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        for cs in css:
            mdss = el.componentDataSources(cs)
            print mdss
            cmps.extend(mdss)
        self.assertEqual(cmps,[dsname[0],dsname[2],dsname[3]])

        self.assertEqual(long(el.version.split('.')[-1]), revision +7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el,xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % (xds[0] % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % (xds[1] % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,xds[3] % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[2],dsname[3]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources_man(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el,xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % (xds[0] % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % (xds[1] % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,xds[3] % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        el.setMandatoryComponents([name[0]])

        css = [name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[2],dsname[3]]))

        el.unsetMandatoryComponents([name[0]])

        self.assertEqual(long(el.version.split('.')[-1]), revision +9)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources_external(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[2],dsname[3]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision+7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources_external_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[1]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision+5)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources_external_2_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3"><datasource>%s%s</datasource></field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0], '__unnamed__0', dsname[1]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision+5)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_componentsDataSources_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>'
               % (xds[0] % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>'
               % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        cmps = []
        mdss = el.componentsDataSources(css)
        print mdss
        cmps.extend(mdss)
        self.assertEqual(sorted(cmps), sorted([dsname[0],dsname[2],dsname[3]]))

        self.assertEqual(long(el.version.split('.')[-1]), revision +7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])
        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field></definition>'% ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_var_1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = [
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % (xds[0] % dsname[0]),
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % ("$datasources.$var.source"),
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % ("$datasources.%s" % dsname[0])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[i] for i in range(len(xml))]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "source":"%s"}' % dsname[0]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertEqual(gxml.replace("?>\n<", "?><"), '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>'   % ( dsname[0]))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_var_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name5" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name=""/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name=""/>  </datasource> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r2"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % (dsname[0],dsname[1],dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r2"/>  </datasource> </field></definition>' % (dsname[0],dsname[0],dsname[1])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_2_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3"><datasource>%s%s</datasource></field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]
        print "AVAIL2", el.availableDataSources()

        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print "GXML2:\n", gxml
        self.assertTrue((gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource>   \n   <datasource name="%s" type="CLIENT">    <record name="r1"/>   </datasource>   \n   <datasource name="%s" type="CLIENT">    <record name="r2"/>   </datasource>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % (dsname[0], dsname[1], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource>   \n   <datasource name="%s" type="CLIENT">    <record name="r1"/>   </datasource>   \n   <datasource name="%s" type="CLIENT">    <record name="r2"/>   </datasource>  </datasource> </field></definition>'  % (dsname[0], dsname[0], dsname[1]))
)

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_3_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            """<datasource name="%s" type="CLIENT">$datasources.%s$datasources.%s<result>
import nxsconfigserver
ds.result = nxsconfigserver.__version__</result></datasource>"""
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        dsname.append(odsname +'_111')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds or dsname[2] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'
            dsname[2] = rename + '_111'

        for i in range(dsnp):
            if i < 2:
                self.setXML(el, xds[i] % dsname[i])
            else:
                self.setXML(el, xds[i] % (dsname[2], dsname[0], dsname[1]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field></definition>'
               % ("$datasources.%s" % dsname[2])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]
        print "AVAIL2", el.availableDataSources()

        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print "GXML3:\n", gxml

        mxml = gxml.replace(">    ", ">").replace(">   ", ">").replace(">  ", ">").replace("> ", ">")\
            .replace("    <", "<").replace("   <", "<").replace("  <", "<").replace(" <", "<")\
            .replace("?>\n<", "?><")
        self.assertTrue((mxml == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3">\n<datasource name="%s" type="CLIENT">\n<datasource name="%s" type="CLIENT"><record name="r1"/></datasource>\n<datasource name="%s" type="CLIENT"><record name="r2"/></datasource><result>\nimport nxsconfigserver\nds.result = nxsconfigserver.__version__</result></datasource></field><field name="field1">\n<datasource name="%s" type="CLIENT"><record name="r1"/></datasource></field></definition>' % (dsname[2], dsname[0], dsname[1], dsname[0])) |
                        (mxml == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">\n<datasource name="%s" type="CLIENT"><record name="r1"/></datasource></field><field name="field3">\n<datasource name="%s" type="CLIENT">\n<datasource name="%s" type="CLIENT"><record name="r1"/></datasource>\n<datasource name="%s" type="CLIENT"><record name="r2"/></datasource><result>\nimport nxsconfigserver\nds.result = nxsconfigserver.__version__</result></datasource></field></definition>' % (dsname[0], dsname[2], dsname[0], dsname[1])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_definition(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, "<?xml version=\'1.0\'?><definition>%s</definition>" % (xds[i] % dsname[i]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print el.components([name[0], name[2]])
        print "CSS",css
        print "MAND", el.mandatoryComponents()
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man
        revision = long(el.version.split('.')[-1])

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s</field></definition>'% ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'
        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="$var.name3"/></datasource></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource name="%s" type="CLIENT"><record name="$var.name3"/></datasource></field><field name="field4">$datasources.%s</field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_var_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name5" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'
        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="$var.name3"/></datasource></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                         (gxml.replace("?>\n<", "?><") =='<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource name="%s" type="CLIENT"><record name="$var.name3"/></datasource></field><field name="field4">$datasources.%s</field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % (dsname[0],dsname[1],dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource></field><field name="field4">$datasources.%s</field></definition>' % (dsname[0],dsname[0],dsname[1])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_2_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3"><datasource>%s%s</datasource></field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]

        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource>$datasources.%s$datasources.%s</datasource></field><field name="field1">$datasources.%s</field></definition>' % (dsname[0], dsname[1], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource>$datasources.%s$datasources.%s</datasource></field></definition>' % (dsname[0], dsname[0], dsname[1])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_3_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            """<datasource name="%s" type="CLIENT">$datasources.%s$datasources.%s<result>
import nxsconfigserver
ds.result = nxsconfigserver.__version__</result></datasource>"""
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        dsname.append(odsname +'_111')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds or dsname[2] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'
            dsname[2] = rename + '_111'

        for i in range(dsnp):
            if i < 2:
                self.setXML(el, xds[i] % dsname[i])
            else:
                self.setXML(el, xds[i] % (dsname[2], dsname[0], dsname[1]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field></definition>'
               % ("$datasources.%s" % dsname[2])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]
        print "AVAIL2", el.availableDataSources()

        gxml = el.merge(css)
        mxml = gxml.replace(">    ", ">").replace(">   ", ">").replace(">  ", ">").replace("> ", ">")\
                .replace("    <", "<").replace("   <", "<").replace("  <", "<").replace(" <", "<")\
                .replace("?>\n<", "?><")

        self.assertTrue((mxml  == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % (dsname[2],  dsname[0])) |
                        (mxml  == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3">$datasources.%s</field></definition>' % (dsname[0],  dsname[2])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_definition(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, "<?xml version=\'1.0\'?><definition>%s</definition>" % (xds[i] % dsname[i]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print el.components([name[0], name[2]])
        print "CSS",css
        print "MAND", el.mandatoryComponents()
        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s</field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s</field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s</field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

#################################

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0],'<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1],'<definition><group type="NXentry"/><field name="field3"><datasource name="mcs_test_datasource_2" type="CLIENT"><record name="r3" /></datasource></field><field name="field4">\n<datasource name="mcs_test_datasource_3" type="CLIENT"><record name="r4"/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_var(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])
        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0],'<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1],'<definition><group type="NXentry"/><field name="field3"><datasource name="mcs_test_datasource_2" type="CLIENT"><record name="r3" /></datasource></field><field name="field4">\n<datasource name="mcs_test_datasource_3" type="CLIENT"><record name="r4"/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_var_1(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = [
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % (xds[0] % dsname[0]),
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % ("$datasources.$var.source"),
            '<definition><group type="NXentry"/><field name="field">%s</field></definition>' % ("$datasources.%s" % dsname[0])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[i] for i in range(len(xml))]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "source":"%s"}' % dsname[0]
        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),3)
        self.assertEqual(comps[0],'<definition><group type="NXentry"/><field name="field"><datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1" /></datasource></field></definition>')
        self.assertEqual(comps[1],'<definition><group type="NXentry"/><field name="field">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[2],'<definition><group type="NXentry"/><field name="field">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 4)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_var_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="$var.name1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="$var.name5" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.variables = '{"name1":"r1", "name2":"r2", "name3":"r3", "name4":"r4"}'

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0],'<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1],'<definition><group type="NXentry"/><field name="field3"><datasource name="mcs_test_datasource_2" type="CLIENT"><record name="r3" /></datasource></field><field name="field4">\n<datasource name="mcs_test_datasource_3" type="CLIENT"><record name=""/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0], '<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1], '<definition><group type="NXentry"/><field name="field3"><datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1" /></datasource></field><field name="field4">\n<datasource name="mcs_test_datasource_11" type="CLIENT"><record name="r2"/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_2_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3"><datasource>%s%s</datasource></field></definition>'
               % ("$datasources.%s" % dsname[0] ,"$datasources.%s" % dsname[1])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]
        print "AVAIL2", el.availableDataSources()

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0], '<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1], '<definition><group type="NXentry"/><field name="field3"><datasource>\n<datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1"/></datasource>\n<datasource name="mcs_test_datasource_11" type="CLIENT"><record name="r2"/></datasource></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 6)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_3_double(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            """<datasource name="%s" type="CLIENT">$datasources.%s$datasources.%s<result>
import nxsconfigserver
ds.result = nxsconfigserver.__version__</result></datasource>"""
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        dsname.append(odsname +'_1')
        dsname.append(odsname +'_11')
        dsname.append(odsname +'_111')
        rename = odsname
        while dsname[0] in avds or dsname[1] in avds or dsname[2] in avds:
            rename = rename + "_1"
            dsname[0] = rename + '_1'
            dsname[1] = rename + '_11'
            dsname[2] = rename + '_111'

        for i in range(dsnp):
            if i < 2:
                self.setXML(el, xds[i] % dsname[i])
            else:
                self.setXML(el, xds[i] % (dsname[2], dsname[0], dsname[1]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[0] % dsname[0] ,"$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field></definition>'
               % ("$datasources.%s" % dsname[2])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[3]]
        print "AVAIL2", el.availableDataSources()

        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0],'<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1],'<definition><group type="NXentry"/><field name="field3">\n<datasource name="mcs_test_datasource_111" type="CLIENT">\n<datasource name="mcs_test_datasource_1" type="CLIENT"><record name="r1"/></datasource>\n<datasource name="mcs_test_datasource_11" type="CLIENT"><record name="r2"/></datasource><result>\nimport nxsconfigserver\nds.result = nxsconfigserver.__version__</result></datasource></field></definition>')
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_instantiatedComponents_mixed_definition(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, "<?xml version=\'1.0\'?><definition>%s</definition>" % (xds[i] % dsname[i]))
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            self.__ds.append(dsname[i])

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s</field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s</field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s</field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print el.components([name[0], name[2]])
        print "CSS",css
        print "MAND", el.mandatoryComponents()
        comps = el.instantiatedComponents(css)
        self.assertEqual(len(comps),2)
        self.assertEqual(comps[0], '<definition><group type="NXentry"/><field name="field1">\n<datasource name="mcs_test_datasource_0" type="CLIENT"><record name="r1"/></datasource></field></definition>')
        self.assertEqual(comps[1], '<definition><group type="NXentry"/><field name="field3"><datasource name="mcs_test_datasource_2" type="CLIENT"><record name="r3" /></datasource></field><field name="field4">\n<datasource name="mcs_test_datasource_3" type="CLIENT"><record name="r4"/></datasource></field></definition>')

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_switch_none(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource>  <strategy mode="FINAL"/> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="INIT"/> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="INIT"/> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource>  <strategy mode="FINAL"/> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_switch_one(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = '["%s"]' % dsname[0]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource>  <strategy mode="FINAL"/> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="STEP"/> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="STEP"/> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource>  <strategy mode="FINAL"/> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_switch_one_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = '["%s"]' % dsname[2]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource>  <strategy mode="STEP"/> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="INIT"/> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="INIT"/> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource>  <strategy mode="STEP"/> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_mixed_switch_two(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = '["%s", "%s"]' % (dsname[0], dsname[2])
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource>  <strategy mode="STEP"/> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource> </field> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="STEP"/> </field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition> <group type="NXentry"/> <field name="field1">  \n  <datasource name="%s" type="CLIENT">   <record name="r1"/>  </datasource>  <strategy mode="STEP"/> </field> <field name="field3">  <datasource name="%s" type="CLIENT">   <record name="r3"/>  </datasource> </field> <field name="field4">  \n  <datasource name="%s" type="CLIENT">   <record name="r4"/>  </datasource>  <strategy mode="STEP"/> </field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_addlink_one(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                         '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4"><datasource name="%s" type="CLIENT"><record name="r4"/></datasource></field><field name="field1"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource><strategy mode="INIT"/></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_addlink_noentry(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry" /><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry" /><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                         '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4"><datasource name="%s" type="CLIENT"><record name="r4"/></datasource></field><field name="field1"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource><strategy mode="INIT"/></field></definition>'  % ( dsname[2], dsname[3], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_addlink_two(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field><group name="data" type="NXdata" /></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s", "%s"]' % (dsname[0],dsname[2])
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                        '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4"><datasource name="%s" type="CLIENT"><record name="r4"/></datasource></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field3"/><link name="%s" target="/entry:NXentry/field1"/></group><field name="field1"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource><strategy mode="INIT"/></field></group></definition>'  % ( dsname[2], dsname[3], dsname[2], dsname[0], dsname[0]))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

            ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_createConfiguration_addlink_withdata(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field><group name="data" type="NXdata" /></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        self.assertEqual(el.createConfiguration(css), None)
        gxml = self.getXML(el)
        print gxml.replace("?>\n<", "?><")
        try:
            self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                        '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4"><datasource name="%s" type="CLIENT"><record name="r4"/></datasource></field><field name="field1"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource><strategy mode="INIT"/></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        except:
            self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                             '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4"><datasource name="%s" type="CLIENT"><record name="r4"/></datasource></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group><field name="field1"><datasource name="%s" type="CLIENT"><record name="r1"/></datasource><strategy mode="INIT"/></field></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()



    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_switch_none(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        gxml = el.merge(css)
        print gxml
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="INIT"/></field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==  '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s<strategy mode="INIT"/></field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">datasources.%s</datasource><strategy mode="FINAL"/></field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_switch_one(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = "%s" % dsname[0]
        gxml = el.merge(css)
        print gxml
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="STEP"/></field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s<strategy mode="STEP"/></field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s<strategy mode="FINAL"/></field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_switch_one_2(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = "%s" % dsname[2]
        gxml = el.merge(css)
        self.assertTrue((gxml.replace("?>\n<", "?><") == '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="STEP"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="INIT"/></field></definition>' % ( dsname[2], dsname[3], dsname[0])) |
                        (gxml.replace("?>\n<", "?><") ==   '<?xml version="1.0" ?><definition><group type="NXentry"/><field name="field1">$datasources.%s<strategy mode="INIT"/></field><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource></field><field name="field4">$datasources.%s<strategy mode="STEP"/></field></definition>' % ( dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_mixed_switch_two(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group type="NXentry"/><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group type="NXentry"/><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.stepdatasources = "%s %s" % (dsname[0], dsname[2])
        gxml = el.merge(css)
        print gxml
        self.assertTrue(
            (gxml.replace("?>\n<", "?><") ==
             '<?xml version="1.0" ?><definition><group type="NXentry"/>'
             '<field name="field3"><datasource name="%s" type="CLIENT">'
             '<record name="r3"/></datasource><strategy mode="STEP"/></field>'
             '<field name="field4">$datasources.%s</field>'
             '<field name="field1">$datasources.%s<strategy mode="STEP"/>'
             '</field></definition>' % (dsname[2], dsname[3], dsname[0])) |
            (gxml.replace("?>\n<", "?><") ==
             '<?xml version="1.0" ?><definition><group type="NXentry"/>'
             '<field name="field1">$datasources.%s</field>'
             '<field name="field3"><datasource name="%s" type="CLIENT">'
             '<record name="r3"/></datasource></field><field name="field4">'
             '$datasources.%s</field></definition>'
             % (dsname[0], dsname[2], dsname[3])))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_addlink_one(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        gxml = el.merge(css)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                         '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="INIT"/></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_addlink_noentry(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry" /><field name="field1">%s<strategy mode="INIT"/></field></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"/><field name="field2">%s<strategy mode="FINAL"/></field></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry" /><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        gxml = el.merge(css)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                         '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"/><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="INIT"/></field></definition>'  % ( dsname[2], dsname[3], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

    ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_addlink_two(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field><group name="data" type="NXdata" /></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s", "%s"]' % (dsname[0],dsname[2])
        gxml = el.merge(css)
        print gxml.replace("?>\n<", "?><")
        self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                        '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field3"/><link name="%s" target="/entry:NXentry/field1"/></group><field name="field1">$datasources.%s<strategy mode="INIT"/></field></group></definition>'  % ( dsname[2], dsname[3], dsname[2], dsname[0], dsname[0]))

        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()

            ## creatConf test
    # \brief It tests XMLConfigurator
    def ttest_merge_addlink_withdata(self):
        fun = sys._getframe().f_code.co_name
        print "Run: %s.%s() " % (self.__class__.__name__, fun)

        el = self.openConf()
        man = el.mandatoryComponents()
        el.unsetMandatoryComponents(man)
        self.__man += man

        revision = long(el.version.split('.')[-1])

        avc = el.availableComponents()

        xds  = [
            '<datasource name="%s" type="CLIENT"><record name="r1" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r2" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r3" /></datasource>',
            '<datasource name="%s" type="CLIENT"><record name="r4" /></datasource>'
            ]

        odsname = "mcs_test_datasource"
        avds = el.availableDataSources()
        self.assertTrue(isinstance(avds, list))
        dsnp = len(xds)
        dsname = []
        for i in range(dsnp):

            dsname.append(odsname +'_%s' % i)
            while dsname[i] in avds:
                dsname[i] = dsname[i] + '_%s' %i

        for i in range(dsnp):
            self.setXML(el, xds[i] % dsname[i])
            self.assertEqual(el.storeDataSource(dsname[i]), None)
            print "DS store", dsname[i]
            self.__ds.append(dsname[i])

        print "AVAIL", el.availableDataSources()

        oname = "mcs_test_component"
        self.assertTrue(isinstance(avc, list))
        xml = ['<definition><group name="entry" type="NXentry"><field name="field1">%s<strategy mode="INIT"/></field></group></definition>' % ("$datasources.%s" % dsname[0]),
               '<definition><group  name="entry" type="NXentry"><field name="field2">%s<strategy mode="FINAL"/></field></group></definition>' % ("$datasources.%s" % dsname[1]),
               '<definition><group  name="entry" type="NXentry"><field name="field3">%s<strategy mode="FINAL"/></field><field name="field4">%s</field><group name="data" type="NXdata" /></group></definition>'
               % (xds[2] % dsname[2] ,"$datasources.%s" % dsname[3])
               ]

        np = len(xml)
        name = []
        for i in range(np):

            name.append(oname +'_%s' % i)
            while name[i] in avc:
                name[i] = name[i] + '_%s' %i
#        print avc

        for i in range(np):
            self.setXML(el, xml[i])
            self.assertEqual(el.storeComponent(name[i]), None)
            self.__cmps.append(name[i])

        css = [name[0], name[2]]
        print "AVAIL2", el.availableDataSources()

        el.linkdatasources = '["%s"]' % dsname[0]
        gxml = el.merge(css)
        print gxml.replace("?>\n<", "?><")
        try:
            self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                        '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><field name="field1">$datasources.%s<strategy mode="INIT"/></field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        except:
            self.assertEqual(gxml.replace("?>\n<", "?><").replace(" \n ","").replace(">    <","><").replace(">   <","><").replace(">  <","><").replace("> <","><"),
                             '<?xml version="1.0" ?><definition><group name="entry" type="NXentry"><field name="field3"><datasource name="%s" type="CLIENT"><record name="r3"/></datasource><strategy mode="FINAL"/></field><field name="field4">$datasources.%s</field><group name="data" type="NXdata"><link name="%s" target="/entry:NXentry/field1"/></group><field name="field1">$datasources.%s<strategy mode="INIT"/></field></group></definition>'  % ( dsname[2], dsname[3], dsname[0], dsname[0]))
        self.assertEqual(long(el.version.split('.')[-1]), revision + 7)
        el.setMandatoryComponents(man)
        el.close()




if __name__ == '__main__':
    unittest.main()
