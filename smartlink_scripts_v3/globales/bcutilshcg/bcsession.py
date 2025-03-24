'''
Manage a Breadcrumb session
===========================
'''

import socket
import ssl
import struct
import hashlib
import uuid
from bcapihcg import Message_pb2
from bcapihcg import Common_pb2
import json
import subprocess
import ipaddress

SESSION_ROLE_CO     = Common_pb2.CO
SESSION_ROLE_ADMIN  = Common_pb2.ADMIN
SESSION_ROLE_VIEW   = Common_pb2.VIEW

BCMSG_DEFAULT_SIZE_LIMIT = 1000000


def user_role(username):
    if username == 'co':
        return SESSION_ROLE_CO
    elif username == 'admin':
        return SESSION_ROLE_ADMIN
    elif username == 'view':
        return SESSION_ROLE_VIEW
    raise ValueError('user: {} does not have a role'.format(username))


class BcSessionError(Exception):
    pass


class BcSession(object):
    def __init__(self):
        """
        Provides an interface for communicating with supported Rajant
        Breadcrumbs
        """
        self._instance_id = str(uuid.uuid4())
        self._sequence_no = 0
        self._sslctx = None
        self._ssock = None
        self.started = False
        self.target = None
        self.port = None
        self.timeout = None

    def start(self, target, port=2300, role=SESSION_ROLE_CO, passphrase='',
              timeout=5):
        '''
        Start a session with a target breadcrumb:
        target = the target hostname, port = serivce port,
        role = one of SESSION_ROLE_*,
        passphrase = string, timeout = timeout in seconds

        A BcSessionError exception will be thrown for session errors
        '''
        self.target = target
        self.port = port
        self.role = role
        self.timeout = timeout
        # setup ssl context
        self._sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self._sslctx.options |= ssl.OP_NO_SSLv2
        self._sslctx.options |= ssl.OP_NO_SSLv3
        # setup ssl socket
        addr = socket.getaddrinfo(self.target, self.port)[0]
        """
        print("-------------------------------direc es")
        print(addr)
        """
        sock = socket.socket(addr[0], socket.SOCK_STREAM)
        self._ssock = self._sslctx.wrap_socket(sock)
        self._ssock.settimeout(self.timeout)
        self._ssock.connect(addr[-1])
        # handle challenge
        challenge = self.recvmsg()
        self._sequence_no = challenge.sequenceNumber
        if not challenge.HasField('auth'):
            raise BcSessionError('''missing authentication challenge
            from breadcrumb''')
        sha = hashlib.sha384()
        sha.update(passphrase.encode('utf-8'))
        sha.update(challenge.auth.challengeOrResponse)
        bcm_login = Message_pb2.BCMessage()
        bcm_login.auth.action = Message_pb2.BCMessage.Auth.LOGIN
        bcm_login.auth.role = self.role
        bcm_login.auth.challengeOrResponse = sha.digest()
        bcm_login.auth.appInstanceID = self._instance_id
        bcm_login.auth.compressionMask = 0
        self.sendmsg(bcm_login)
        """
        print("in:")
        print(bcm_login)
        """
        bcm_login = self.recvmsg()
        """
        print("out:")
        print(bcm_login )
        """
        if not bcm_login.HasField('authResult'):
            raise BcSessionError('expecting authentication result')
        if bcm_login.authResult.status != Message_pb2.BCMessage.Result.SUCCESS:
            raise BcSessionError(bcm_login.authResult.description)
        self.started = True

    def stop(self):
        '''
        Stop the session
        '''
        self.target = None
        self.port = None
        self.timeout = None
        self.started = False
        if self._ssock:
            self._ssock.close()
            self._ssock = None
            self._sequence_no = 0
            del self._sslctx
            self._sslctx = None

    def sendmsg(self, breadcrumb_message):
        '''
        Send a message to the breadcrumb
        breadcrumb_message = a Message_pb2.BCMessage message object
        '''
        bcmsg = breadcrumb_message
        bcmsg.sequenceNumber = self._sequence_no
        # struct.pack(fmt, wire_len, compressionMask, rsrvd, rsrvd, rsrvd)
        bchdr = struct.pack('!LBBBB', bcmsg.ByteSize(), 0, 0, 0, 0)
        self._ssock.sendall(bchdr + bcmsg.SerializeToString())
        self._sequence_no += 1
        return None

    def recvmsg(self, sizelimit=BCMSG_DEFAULT_SIZE_LIMIT):
        '''
        Read a pending message from the breadcrumb
        returns a Message_pb2.BCMessage message object read from the breadcrumb
        A BcSessionError exception will be thrown for session errors
        '''

        bcmsghdrlen = 8
        hdr = self._ssock.recv(bcmsghdrlen)

        if len(hdr) < bcmsghdrlen:
            raise BcSessionError('unexpected header size from socket')
        hdr = struct.unpack('!LBBBB', hdr)
        pldsize = hdr[0]
        if pldsize > sizelimit:
            raise BcSessionError('size limit exceeded {}'.format(pldsize))
        pld = b''
        while len(pld) < pldsize:
            data_read = self._ssock.recv(pldsize - len(pld))
            if not data_read:
                raise BcSessionError('no data was read; assuming closed connection')
            pld += data_read
            """
            print("lect_data es:")
            print(pldsize)
            print(len(pld))
            """
        bcm = Message_pb2.BCMessage()
        bcm.ParseFromString(pld)
        return bcm
