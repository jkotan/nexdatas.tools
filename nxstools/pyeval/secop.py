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
#

"""  pyeval helper functions for SECoP """

import json
import socket
import select
import threading


class SocketHolder(object):

    """ socket holder """

    def __init__(self, sckt):
        """ constructor

        :param sckt: system socket
        :type sckt: :class:`socket.socket`
        """
        self.__sckt = sckt

    def get(self):
        """ socket getter

        :returns: system socket
        :rtype: :class:`socket.socket`
        """
        return self.__sckt

    def __del__(self):
        """  socket closer
        """
        socket.close(self.__sckt)
        self.__sckt = None


class SecopGroup(object):

    """ socket holder """

    def __init__(self, group):
        """ constructor

        :param group: secop group name
        :type group: :obj:`str`
        """
        self.__group = group

        #: (:class:`threading.Lock`) threading lock
        self.lock = threading.Lock()
        #: (:obj:`int`) counter of steps
        self.counter = -1

    def getData(self, cmd, host=None, port=None, timeout=None,
                access=None,
                globallock=None, commonblock=None):
        """ create a socket end execute the command with the group result

        :param counter: counts of scan steps
        :type counter: :obj:`int`
        :param cmd: command
        :type cmd: :obj:`str`
        :param host: secop host name
        :type host: :obj:`str`
        :param port: secop port name
        :type port: :obj:`int`
        :param timeout: minial tiemout
        :type timeout: :obj:`float`
        :param access: secop group name
        :type access: :obj:`list`< :obj:`str` or :obj:`int`>
                  or :obj:`tuple`< :obj:`str` or :obj:`int`>
        :param globallock: global lock
        :type globallock: :class:`threading.Lock`
        :param commonblock: common block
        :type commonblock: :obj:`dict`
        :returns: json string
        :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
        """
        return


def secop_send(cmd, sckt, timeout=None):
    """ sends a command, reads the reply and returns a result

    :param cmd: command
    :type cmd: :obj:`str`
    :param sckt: system socket
    :type sckt: :class:`socket.socket`
    :param timeout: minial tiemout
    :type timeout: :obj:`float`
    :returns: json string
    :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
    """
    sckt.send((cmd + "\n").encode())
    buffer = ""
    timeout = float(timeout or 0.001)
    for tofactor in [1, 10, 100, 1000, 3000]:
        tout = tofactor * timeout
        while True:
            infds, outfds, errfds = select.select(
                [sckt], [], [], tout)
            if len(infds) == 0:
                break
            buffer = buffer + sckt.recv(1024).decode()
        lst = buffer.split(' ')
        com = ''.join(lst[2:]).strip()
        try:
            argout = json.loads(com)
            break
        except Exception:
            argout = buffer.strip()
    return argout


def secop_socket(host=None, port=None,
                 globallock=None, commonblock=None):
    """ sends a command, reads the reply and returns a result

    :param host: secop host name
    :type host: :obj:`str`
    :param port: secop port name
    :type port: :obj:`int`
    :param globallock: global lock
    :type globallock: :class:`threading.Lock`
    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :returns: system socket
    :rtype: :class:`socket.socket`
    """
    host = host or socket.gethostname()
    port = int(port or 5000)
    if globallock is None or not isinstance(commonblock, dict):
        sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    else:
        name = "secop_%s:%s" % (host, port)
        with globallock:
            if name in commonblock.keys() and \
               isinstance(commonblock[name], SocketHolder):
                sckt = commonblock[name].get()
            else:
                sckt = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                commonblock[name] = SocketHolder(sckt)
    try:
        sckt.connect((host, port))
    except Exception as e:
        sckt.close()
        raise e
    return sckt


def secop_cmd(cmd, host=None, port=None, timeout=None,
              globallock=None, commonblock=None):
    """ create a socket end execute the command

    :param cmd: command
    :type cmd: :obj:`str`
    :param host: secop host name
    :type host: :obj:`str`
    :param port: secop port name
    :type port: :obj:`int`
    :param timeout: minial tiemout
    :type timeout: :obj:`float`
    :param globallock: global lock
    :type globallock: :class:`threading.Lock`
    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :returns: json string
    :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
    """
    res = None
    try:
        try:
            sckt = secop_socket(
                host, port, globallock, commonblock)
            res = secop_send(cmd, sckt, timeout)
        except Exception:
            sckt = secop_socket(host, port)
            res = secop_send(cmd, sckt, timeout)
        if globallock is None or not isinstance(commonblock, dict):
            sckt.close()
    except Exception:
        sckt.close()
    return res


def secop_group_cmd(cmd, host=None, port=None, timeout=None,
                    group=None, access=None,
                    globallock=None, commonblock=None):
    """ create a socket end execute the command with the group result

    :param cmd: command
    :type cmd: :obj:`str`
    :param host: secop host name
    :type host: :obj:`str`
    :param port: secop port name
    :type port: :obj:`int`
    :param timeout: minial tiemout
    :type timeout: :obj:`float`
    :param group: secop group name
    :type group: :obj:`str`
    :param access: secop group name
    :type access: :obj:`list`< :obj:`str` or :obj:`int`>
                  or :obj:`tuple`< :obj:`str` or :obj:`int`>
    :param globallock: global lock
    :type globallock: :class:`threading.Lock`
    :param commonblock: common block
    :type commonblock: :obj:`dict`
    :returns: json string
    :rtype: :obj:`dict` <:obj:`str`, :obj:`any`>
    """
    res = None
    if group is None or access is None or \
       globallock in None or commonblock is None:
        return secop_cmd(cmd, host, port, timeout, globallock, commonblock)
    name = "_secop_%s" % group
    sgroup = None
    with globallock:
        if name in commonblock.keys() and \
           isinstance(commonblock[name], SecopGroup):
            sgroup = commonblock[name].get()
        else:
            sgroup = SecopGroup(name)
            commonblock[name] = sgroup

    res = sgroup.getData(cmd, host, port, timeout, access,
                         globallock, commonblock)
    return res
