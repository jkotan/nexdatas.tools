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

"""  xml templates """


#: (:obj:`dict` <:obj:`str` , :obj:`dict` <:obj:`str` , :obj:`str` > >)
#:     standatd component template variables
#:     and its [default value, doc string]
standardComponentVariables = {
    'slit': {
        'xgap': {
            'default': None,
            'doc': "horizontal gap (datasource)"
        },
        'ygap': {
            'default': None,
            'doc': "vertical gap (datasource)"
        },
        'xoffset': {
            'default': None,
            'doc': "horizontal offset (datasource)"
        },
        'yoffset': {
            'default': None,
            'doc': "vertiacal offset (datasource)"
        },
        'left': {
            'default': None,
            'doc': "left blade position (datasource)"
        },
        'right': {
            'default': None,
            'doc': "right blade position (datasource)"
        },
        'bottom': {
            'default': None,
            'doc': "bottom blade position (datasource)"
        },
        'top': {
            'default': None,
            'doc': "top blade position (datasource)"
        }
    },
    'source': {
        'beamcurrent': {
            'default': None,
            'doc': "ring beam current (datasource)"
        },
        'sourceenergy': {
            'default': None,
            'doc': "ring beam energy (datasource)"
        }
    },
    'undulator': {
        'energy': {
            'default': None,
            'doc': "undulator energy (datasource)"
        },
        'gap': {
            'default': None,
            'doc': "separation between opposing pairs of magnetic pole"
            " (datasource)"
        },
        'taper': {
            'default': None,
            'doc': "gap difference between upstream and downstream ends"
            " of the insertion device (datasource)"
        },
        'harmonic': {
            'default': None,
            'doc': "undulator harmonic (datasource)"
        },
    },
    'default': {
        'shortname': {
            'default': "P09",
            'doc': "beamline short name (string)"
        },
        'longname': {
            'default': "P09 Resonant Scattering and Diffraction beamline",
            'doc': "beamline long name (string)"
        },
        'sourcename': {
            'default': "PETRA III",
            'doc': "source name (string)"
        },
        '__tangohost__': {
            'default': "localhost",
            'doc': "tango host (string)"
        },
        '__tangoport__': {
            'default': "10000",
            'doc': "tango port (string)"
        },
        '__configdevice__': {
            'default': "nxs/configserver/localhost",
            'doc': "configuration server device name (string)"
        },
    },
    'dcm': {
        'energy': {
            'default': None,
            'doc': "monochromator energy (datasource)"
        },
        'lat': {
            'default': None,
            'doc': "horizontal lattice translation of the first cristal"
            " (datasource)"
        },
        'yaw': {
            'default': None,
            'doc': "yaw rotation of the first cristal"
            " (datasource)"
        },
        'roll1': {
            'default': None,
            'doc': "roll rotation of the first cristal"
            " (datasource)"
        },
        'roll2': {
            'default': None,
            'doc': "roll rotation of the second cristal"
            " (datasource)"
        },
        'pitch2': {
            'default': None,
            'doc': "pitch rotation of the second cristal"
            " (datasource)"
        },
        'perp2': {
            'default': None,
            'doc': "vertical translation of the second cristal"
            " (datasource)"
        },
        'par2': {
            'default': None,
            'doc': "beam parallel translation of the second cristal"
            " (datasource)"
        },
        'braggangle': {
            'default': None,
            'doc': "bragg angle"
            " (datasource)"
        },
        'jack1': {
            'default': None,
            'doc': "first vertical jack of table"
            " (datasource)"
        },
        'jack2': {
            'default': None,
            'doc': "second vertical jack of table"
            " (datasource)"
        },
        'jack3': {
            'default': None,
            'doc': "third vertical jack of table"
            " (datasource)"
        },
        'table': {
            'default': None,
            'doc': "vertical position of table"
            " (datasource)"
        },
        'oxfordhorizontal': {
            'default': None,
            'doc': " horizontal translation"
            " (datasource)"
        },
        'exitoffset': {
            'default': None,
            'doc': " exit offset"
            " (datasource)"
        },
        'theta': {
            'default': None,
            'doc': "theta angle"
            " (datasource)"
        },
        'dcmdevice': {
            'default': None,
            'doc': "FMBOxfDCMEnergy tango device"
            " (string)"
        },
    },
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
standardComponentTemplateFiles = {
    'slit': ['slit.xml'],
    'source': ['source.xml'],
    'undulator': ['undulator.xml'],
    'default': [
        'default.xml',
        'sample_name.ds.xml',
        'chemical_formula.ds.xml',
        'beamtime_id.ds.xml',
        'start_time.ds.xml',
        'end_time.ds.xml',
        'nexdatas_version.ds.xml',
        'nexdatas_configuration.ds.xml',
        'title.ds.xml',
    ],
    'dcm': [
        'dcm.xml',
        'dcm_reflection.ds.xml',
    ],
}

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     xml template files of modules
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

#: (:obj:`dict` <:obj:`str` , :obj:`list` <:obj:`str`> >)
#:     important attributes of modules
moduleMultiAttributes = {
    'pco': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pcoedge': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
        'FileDir', 'FilePostfix', 'FilePrefix', 'FileStartNum',
        'Binning_x', 'Binning_y', 'ROI_x_min', 'ROI_x_max',
        'ROI_y_min', 'ROI_y_max', 'Pixelrate', 'ADCs',
        'CoolingTemp', 'CoolingTempSet', 'ImageTimeStamp',
        'RecorderMode',
    ],
    'pco4000': [
        'DelayTime', 'ExposureTime', 'NbFrames', 'TriggerMode',
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
