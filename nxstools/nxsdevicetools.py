#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2016 DESY, Jan Kotanski <jkotan@mail.desy.de>
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
#

""" NDTS TANGO device tools """

import sys
import os
import time


PYTANGO = False
try:
    import PyTango
    PYTANGO = True
except:
    pass

#: attributes of device modules to acquire with elements:
#  'module': [<sardana_pool_attr>, <original_tango_attr>]
moduleAttributes = {
    'counter_tango': ['Value', 'Counts'],
    'dgg2': ['Value', 'SampleTime'],
    'mca_8701': ['Value', 'Data'],
    'mca_sis3302new': ['Value', 'Data'],
    'mca_sis3302': ['Value', 'Data'],
    'mythenroi': ['Value', None],
    'mca8715roi': ['Value', None],
    'sis3302roi': ['Value', None],
    'sis3610': ['Value', 'Value'],
    'sis3820': ['Value', 'Counts'],
    'tangoattributectctrl': ['Value', None],
    'tip551': ['Value', 'Voltage'],
    'tip830': ['Value', 'Counts'],
    'vfcadc': ['Value', 'Counts'],
    'xmcd': ['Value', None],
}

#: xml template files of modules
moduleTemplateFiles = {
    'pilatus100k': ['pilatus.xml',
                    'pilatus_postrun.ds.xml',
                    'pilatus100k_description.ds.xml',
                    'pilatus_filestartnum_cb.ds.xml'],
    'pilatus300k': ['pilatus.xml',
                    'pilatus_postrun.ds.xml',
                    'pilatus300k_description.ds.xml',
                    'pilatus_filestartnum_cb.ds.xml'],
    'pilatus1m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus1m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus2m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus2m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus6m': ['pilatus.xml',
                  'pilatus_postrun.ds.xml',
                  'pilatus6m_description.ds.xml',
                  'pilatus_filestartnum_cb.ds.xml'],
    'pilatus': ['pilatus.xml',
                'pilatus_postrun.ds.xml',
                'pilatus_description.ds.xml',
                'pilatus_filestartnum_cb.ds.xml'],
    'pco': ['pco.xml',
            'pco_postrun.ds.xml',
            'pco_description.ds.xml',
            'pco_filestartnum_cb.ds.xml'],
    'pcoedge': ['pco.xml',
                'pco_postrun.ds.xml',
                'pco_description.ds.xml',
                'pco_filestartnum_cb.ds.xml'],
    'pco4000': ['pco.xml',
                'pco_postrun.ds.xml',
                'pco_description.ds.xml',
                'pco_filestartnum_cb.ds.xml'],
    'lambda': ['lambda.xml',
               'lambda_external_data.ds.xml'],
    'lambda2m': ['lambda2m.xml',
                 'lambda2m_m1_external_data.ds.xml',
                 'lambda2m_m2_external_data.ds.xml',
                 'lambda2m_m3_external_data.ds.xml'],
    'perkinelmerdetector': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'perkinelmer': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'pedetector': [
        'perkinelmerdetector.xml',
        'perkinelmerdetector_postrun.ds.xml',
        'perkinelmerdetector_description.ds.xml',
        'perkinelmerdetector_fileindex_cb.ds.xml'
    ],
    'marccd': ['marccd.xml',
               'marccd_postrun.ds.xml'],
}

#: important attributes of modules
moduleMultiAttributes = {
    'pco': [
        'DelayTime',  'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pcoedge': [
        'DelayTime',  'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pco4000': [
        'DelayTime',  'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pilatus100k': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus300k': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus1m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus2m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pilatus6m': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'pedetector': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'perkinelmerdetector': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'perkinelmer': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1', 'CameraGain',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction'
    ],
    'mythen': [
        'Counts1', 'Counts2', 'CountsMax', 'CountsTotal', 'ExposureTime',
        'FileDir', 'FileIndex', 'FilePrefix', 'LastImage', 'RoI1', 'RoI2'
    ],
    'lambda': [
        'TriggerMode', 'ShutterTime', 'DelayTime', 'FrameNumbers', 'ThreadNo',
        'EnergyThreshold', 'OperatingMode', 'ConfigFilePath', 'SaveAllImages',
        'FilePrefix', 'FileStartNum', 'FilePreExt', 'FilePostfix',
        'SaveFilePath', 'SaveFileName', 'LatestImageNumber', 'LiveMode',
        'TotalLossFrames', 'CompressorShuffle', 'CompressionRate',
        'CompressionEnabled', 'Layout', 'ShutterTimeMax', 'ShutterTimeMin',
        'Width', 'Height', 'Depth', 'LiveFrameNo', 'DistortionCorrection',
        'LiveLastImageData'
    ],
    'lambda2m': [
        'TriggerMode', 'ShutterTime', 'DelayTime', 'FrameNumbers', 'ThreadNo',
        'EnergyThreshold', 'OperatingMode', 'ConfigFilePath', 'SaveAllImages',
        'FilePrefix', 'FileStartNum', 'FilePreExt', 'FilePostfix',
        'SaveFilePath', 'SaveFileName', 'LatestImageNumber', 'LiveMode',
        'TotalLossFrames', 'CompressorShuffle', 'CompressionRate',
        'CompressionEnabled', 'Layout', 'ShutterTimeMax', 'ShutterTimeMin',
        'Width', 'Height', 'Depth', 'LiveFrameNo', 'DistortionCorrection',
        'LiveLastImageData'
    ],
    'pedetector': [
        'BinningMode', 'FileIndex', 'ExposureTime', 'SkippedAtStart',
        'SummedSaveImages', 'SkippedBetweenSaved', 'FilesAfterTrigger',
        'FilesBeforeTrigger', 'SummedDarkImages', 'OutputDirectory',
        'FilePattern', 'FileName', 'LogFile', 'UserComment1',
        'UserComment2', 'UserComment3', 'UserComment4', 'SaveRawImages',
        'SaveDarkImages', 'PerformIntegration', 'SaveIntegratedData',
        'SaveSubtracted', 'PerformDarkSubtraction', 'CameraGain'

    ],
    'pilatus': [
        'DelayTime', 'ExposurePeriod', 'ExposureTime', 'FileDir',
        'FilePostfix', 'FilePrefix', 'FileStartNum', 'LastImageTaken',
        'NbExposures', 'NbFrames'],
    'marccd': [
        'FrameShift', 'SavingDirectory', 'SavingPostfix', 'SavingPrefix'],
}

#: modules of 2d detectors
TwoDModules = [
    'pilatus100k', 'pilatus300k', 'pilatus1m',
    'pilatus2m', 'pilatus6m', 'pco4000', 'perkinelmerdetector',
    'lambda', 'pedetector', 'perkinelmer',
    'pco', 'pcoedge', 'marccd', 'perkinelmer',
    #
    'lcxcamera',  'limaccd', 'eigerpsi',
    'eigerdectris'
]


#: modules of motors
motorModules = [
    'absbox', 'motor_tango', 'kohzu', 'smchydra', 'lom', 'oms58', 'e6c',
    'omsmaxv', 'spk', 'pie710', 'pie712', 'e6c_p09_eh2'
    #
    #    'analyzerep01', 'tth', 'atto300',  'phaseretarder',
    #    'hexa',
    #    'tm', 'cube', , 'piezonv40', 'smaractmcs',
    #    'slt', 'bscryotempcontrolp01',
    #    'dcm_energy', 'elom', 'diffracmu',  'tcpipmotor',
    #    'galil_dmc', 'pico8742', 'oxfcryo700ctrl', 'analyzer', 'nfpaxis',
    #    'smarpod', 'mult',
    #
    #    'oxfcryo700',
]

#: counter/timer modules
CTModules = [
    'mca8715roi', 'onedroi', 'sis3820', 'sis3302roi',
    'xmcd', 'vfcadc', 'mythenroi', 'mhzdaqp01', 'dgg2',
    'tangoattributectctrl'
]

#: modules of 0D detectors
ZeroDModules = ['tip830']

#: modules of 1D detectors
OneDModules = ['mca_xia']

#: IO register modules
IORegModules = ['sis3610']


for mn in motorModules:
    moduleAttributes[mn] = ['Position', 'Position']

for nm in CTModules + ZeroDModules + OneDModules:
    if nm not in moduleAttributes:
        moduleAttributes[nm] = ['Value', None]


def generateDeviceNames(prefix, first, last, minimal=False):
    """ generates device names

    :param prefix: device name prefix5
    :param first: first device index
    :param last: last device index
    :returns: device names
    """
    names = []
    if prefix.strip():
        for i in range(first, last + 1):
            if not minimal:
                names.append(prefix + ("0" if len(str(i)) == 1 else "")
                             + str(i))
            else:
                names.append(prefix + str(i))
    return names


def getAttributes(device, host=None, port=10000):
    """ provides a list of device attributes

    :param device: tango device name
    :param host: device host
    :param port: device port
    :returns: list of device attributes

    """
    if host:
        dp = PyTango.DeviceProxy("%s:%s/%s" % (host, port, device))
    else:
        dp = PyTango.DeviceProxy(device)
    attr = dp.attribute_list_query()
    return [at.name for at in attr if at.name not in ['State', 'Status']]


def openServer(device):
    """ opens connection to the configuration server

    :param configuration: server device
    :returns: configuration server proxy
    """
    found = False
    cnt = 0
    # spliting character
    try:
        #: configuration server proxy
        cnfServer = PyTango.DeviceProxy(device)
    except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
        found = True

    if found:
        sys.stderr.write(
            "Error: Cannot connect into the server: %s\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    while not found and cnt < 1000:
        if cnt > 1:
            time.sleep(0.01)
        try:
            if cnfServer.state() != PyTango.DevState.RUNNING:
                found = True
        except (PyTango.DevFailed, PyTango.Except, PyTango.DevError):
            time.sleep(0.01)
            found = False
        cnt += 1

    if not found:
        sys.stderr.write("Error: Setting up %s takes to long\n" % device)
        sys.stderr.flush()
        sys.exit(0)

    return cnfServer


def storeDataSource(name, xml, server):
    """ stores datasources

    :param name: datasource name
    :param xml: datasource xml string
    :param server: configuration server
    """
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreDataSource(str(name))


def getServerTangoHost(server):
    """ fetches the server tango host

    :param server: tango server
    :returns: tango host
    """
    proxy = openServer(server)
    host = proxy.get_db_host()
    port = proxy.get_db_port()
    shost = str(host).split(".")
    if len(shost) > 0:
        host = shost[0]
    return "%s:%s" % (host, port)


def getDataSourceComponents(server):
    """ gets datasource components

    :param server: configuration server
    :returns: dictionary with datasource components
    """
    dscps = {}
    proxy = openServer(server)
    proxy.Open()
    acps = proxy.availableComponents()
    for cp in acps:
        try:
            dss = proxy.componentDataSources(cp)
            for ds in dss:
                if ds not in dscps:
                    dscps[ds] = []
                dscps[ds].append(cp)
        except Exception as e:
            sys.stderr.write(str(e))
            sys.stderr.write(
                "Error: Internal error of the %s component\n" % cp)
            sys.stderr.flush()
    return dscps


def storeComponent(name, xml, server):
    """ stores components

    :param name: component name
    :param xml: component xml string
    :param server: configuration server
    """
    proxy = openServer(server)
    proxy.Open()
    proxy.XMLString = str(xml)
    proxy.StoreComponent(str(name))


def getClassName(devicename='NXSConfigServer'):
    """ provides device class name

    :param devicename: device name
    :returns: class name
    """
    try:
        db = PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into %s" % devicename
            + "on host: \n    %s \n " % os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""

    return db.get_class_for_device(devicename)


def getServers(name='NXSConfigServer'):
    """ provides server device names

    :param name: server instance name
    :returns: list of the server device names

    """
    try:
        db = PyTango.Database()
    except:
        sys.stderr.write(
            "Error: Cannot connect into %s" % name
            + "on host: \n    %s \n " % os.environ['TANGO_HOST'])
        sys.stderr.flush()
        return ""

    servers = db.get_device_exported_for_class(name).value_string
    return servers


def remoteCall(server, func, *args, **kwargs):
    """ executes function on remove tango host db setup

    :param server: remove tango server device name
    :param func: executed function
    :param args: function list arguments
    :param kwargs: function dict arguments
    :returns: function result
    """
    lserver = None
    if server and server.strip():
        lserver = server.split("/")[0]
    if lserver:
        lserver = lserver.strip()
    if lserver:
        if ":" not in lserver:
            lserver = lserver + ":10000"
        localtango = os.environ.get('TANGO_HOST')
        os.environ['TANGO_HOST'] = lserver

    res = func(*args, **kwargs)
    if lserver and localtango is not None:
        os.environ['TANGO_HOST'] = localtango
    return res


def listServers(server, name='NXSConfigServer'):
    """ finds server names

    :param name: server instance name
    :returns: server list
    """
    return remoteCall(server, getServers, name)


def findClassName(server, name):
    """ finds class name

    :param name: device name
    :returns: class name
    """
    return remoteCall(server, getClassName, name)


def checkServer(name='NXSConfigServer'):
    """ provides server device name if only one or error in the other case

    :param name: server name
    :returns: server device name or empty string if error appears
    """
    servers = getServers(name)
    if not servers:
        sys.stderr.write(
            "Error: No required server on current host running. \n\n"
            + "    Please specify the server from the other host. \n\n")
        sys.stderr.flush()
        return ""
    if len(servers) > 1:
        sys.stderr.write(
            "Error: More than on %s " % name
            + "on the current host running. \n\n"
            + "    Please specify the server:"
            + "\n        %s\n\n" % "\n        ".join(servers))
        sys.stderr.flush()
        return ""
    return servers[0]


if __name__ == "__main__":
    pass
