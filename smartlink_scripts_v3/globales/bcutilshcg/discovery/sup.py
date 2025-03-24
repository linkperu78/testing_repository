'''
Breadcrumb Discovery using SUP multicast messages
=================================================

'''


import socket
import ctypes
import ctypes.util
import select
import uuid
import os.path
from io import StringIO
from bcapihcg import Sup_pb2
try:
    from configparser import SafeConfigParser
except:
    from ConfigParser import SafeConfigParser
from . import constants

libc = ctypes.CDLL(ctypes.util.find_library('c'))

SUP_MULTICAST_ADDR = 'FF02::1'
SUP_MULTICAST_PORT = 35057


def all_interfaces():
    return [ y for y in filter(lambda x: x != 'lo', os.listdir('/sys/class/net')) ]


def _get_address(addr=None, port=SUP_MULTICAST_PORT):
    #a = socket.getaddrinfo(addr, port, socket.AF_INET6, socket.SOCK_DGRAM, 0, 0)
    #print(a[0][-1])
    return socket.getaddrinfo(addr, port, socket.AF_INET6, socket.SOCK_DGRAM,
                            0, 0)[0][-1]

def if_nametoindex (name):
    try:
        return socket.if_nametoindex(name)
    except:
        assert(isinstance (name, str))
        ret = libc.if_nametoindex (name)
        if not ret:
            raise RuntimeError("Invalid Name")
        return ret

class SupResult(object):
    '''
    Result of a SUP discovery
    '''
    def __init__(self, sup_message = None, sup_source= None):
        if not sup_message: return
        if not sup_source: return
        self.serial = self._prop(sup_message, 'SERIAL')
        self.build = self._prop(sup_message, 'BUILD')
        self.version = self._prop(sup_message, 'VERSION')
        self.network = self._prop(sup_message, 'NETWORK')
        self.platform = self._prop(sup_message, 'PLATFORM')
        self.source_info = sup_source
        self.source = None
        self.source_in6_scopeid = None
        self.source_in6_flowinfo = None
        if len(sup_source) >= 2:
            self.source = sup_source[0]
        if len(sup_source) >= 4:
            self.source_in6_flowinfo = sup_source[2]
            self.source_in6_scopeid = sup_source[3]
        self.source_port = sup_source[1]
        self.port = self._prop(sup_message, 'PORT')
        self.local = True if self._prop(sup_message,'LOCAL') == 'Y' else False

    def _prop(self, sup_message, key):
        ''' Retrieve a property in the sup message '''
        for prop in sup_message.properties:
            if prop.key == key:
                return prop.value
        return None



class SupDiscovery(object):
    '''
    Sup discovery method for locating breadcrumbs on the network
    '''
    def __init__(self, interface = None, service = constants.SERVICE_V11,
                 local = False,
                 scantime = 5000, maxhits = 0, message = None):

        self.ifaces = [ interface ] if interface else [ iface for iface in all_interfaces() ]
        self.ifindexes = set()

        for iface in self.ifaces:
            parser = SafeConfigParser()
            brpath = '/sys/class/net/{}/brport/bridge/uevent'.format(iface)
            if os.path.isfile(brpath):
                with open(brpath) as stream:
                    stream = StringIO('[root]\n' + stream.read())
                    parser.readfp(stream)
                    master = None
                    if parser.has_option('root','INTERFACE'):
                        master = parser.get('root','INTERFACE')
                    if master:
                        self.ifindexes.add(if_nametoindex(master))
            else:
                self.ifindexes.add(if_nametoindex(iface))
        
        #print(f"Red local = {self.ifaces}")

        self.service    = service
        self.local      = local
        self.scantime   = float(scantime) / 1000.
        self.hits       = maxhits
        self.message    = message
        self._clisock   = None
        self._srvsock   = None

    def _setup(self):
        # Initialize a client socket
        self._clisock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self._clisock.setsockopt(socket.IPPROTO_IPV6,
                                 socket.IPV6_MULTICAST_LOOP,
                                 0)
        # Setup server to receive responses
        self._srvsock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self._srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srvsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self._srvsock.bind(_get_address('::'))
        
        #print(f"Server Socket = {self._srvsock}")

    def _on_response(self, response=None, source_address=None):
        sup = Sup_pb2.SupMessage()
        if response:
            try:
                sup.ParseFromString(response)
                if sup.messageType != Sup_pb2.SupMessage.RESPONSE or \
                   sup.service != self.service:
                    return None
                return SupResult(sup, source_address)
            except:
                pass

    def _discover(self):
        sup_message             = Sup_pb2.SupMessage()
        sup_message.header      = Sup_pb2.SupMessage.HEADER_VALUE
        sup_message.messageType = Sup_pb2.SupMessage.REQUEST
        sup_message.service     = self.service
        sup_message.otherPort   = SUP_MULTICAST_PORT

        sup_qid = uuid.uuid4()

        if self.local:
            local = sup_message.properties.add()
            local.key = 'LOCAL'
            local.value = 'Y'

        #print(f"Indexes = {self.ifindexes}")
        for idx in self.ifindexes:
            try:
                sup_message.qid = '{}%{}'.format(idx, sup_qid)
         
                #print(f"{idx} - Message =\n{sup_message}")

                self._clisock.setsockopt(socket.IPPROTO_IPV6,
                                         socket.IPV6_MULTICAST_IF, idx)

                self._clisock.sendto(sup_message.SerializeToString(),
                                     _get_address(SUP_MULTICAST_ADDR,
                                                  SUP_MULTICAST_PORT))
            except:
                pass

        discovered = []
        epoll = select.epoll()
        epoll.register(self._srvsock.fileno(), select.EPOLLIN)
        try:
            scantime = 0.0
            while scantime < self.scantime:
                events = epoll.poll(timeout=1)
                for fd,event in events:
                    if event & select.EPOLLIN:
                        r = self._srvsock.recvfrom(2048)
                        bc = self._on_response(r[0],r[1])
                        if bc:
                            discovered.append(bc)
                scantime += 1
                if self.hits and len(discovered) >= self.hits:
                    break
        finally:
            epoll.unregister(self._srvsock.fileno())
            epoll.close()
            self._srvsock.close()
            self._clisock.close()
        return discovered

    def execute(self):
        '''
        Execute the sup discovery method

        Returns:
            [ SupResults ]
        '''
        self._setup()
        return self._discover()
