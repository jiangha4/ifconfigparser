from __future__ import print_function
import re
import logging
import argparse
import sys

test_text = """bond0     Link encap:Ethernet  HWaddr xx:yy:de:ad:be:ef
            inet addr:10.1.1.1  Bcast:10.1.1.255  Mask:255.255.255.0
            inet6 addr: fe80::1602:ecff:fe6c:6248/64 Scope:Link
            UP BROADCAST RUNNING MASTER MULTICAST  MTU:1500  Metric:1
            RX packets:78754933233 errors:12 dropped:0 overruns:0 frame:12
            TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:0
            RX bytes:83417317310129 (75.8 TiB)  TX bytes:0 (0.0 b)

eth8        Link encap:Ethernet  HWaddr xx:yy:de:ad:be:ef
            UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
            RX packets:56120366224 errors:3 dropped:0 overruns:0 frame:3
            TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:1000
            RX bytes:60876314731840 (55.3 TiB)  TX bytes:0 (0.0 b)

eth10       Link encap:Ethernet  HWaddr xx:yy:de:ad:be:ef
            UP BROADCAST RUNNING SLAVE MULTICAST  MTU:1500  Metric:1
            RX packets:22634567048 errors:9 dropped:0 overruns:0 frame:9
            TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:1000
            RX bytes:22541002608976 (20.5 TiB)  TX bytes:0 (0.0 b)

lo          Link encap:Local Loopback
            inet addr:127.0.0.1  Mask:255.0.0.0
            inet6 addr: ::1/128 Scope:Host
            UP LOOPBACK RUNNING  MTU:65536  Metric:1
            RX packets:968312148 errors:0 dropped:0 overruns:0 frame:0
            TX packets:968312148 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:0
            RX bytes:14257112447341 (12.9 TiB)  TX bytes:14257112447341 (12.9 TiB)"""

# -----------------------------------------------------------------------------
#   Set up CLI arg parser
# -----------------------------------------------------------------------------

parser = argparse.ArgumentParser(description='CLI app to parse ifconfig dump')
parser.add_argument('-d', '--debug', action='store_true', default=False,
                    help='Enable debug output')
args = parser.parse_args()

# -----------------------------------------------------------------------------
#   Set up logger
# -----------------------------------------------------------------------------

log = logging.getLogger('ifconfigParser')
out_hdlr = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
out_hdlr.setFormatter(formatter)
log.addHandler(out_hdlr)

if args.debug:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)

# ----------------------------------------------------------------------------
#   User defined exceptions
# ----------------------------------------------------------------------------

class InterfaceDoesNotExist(Exception):
    pass

class InterfaceParseError(Exception):
    pass

# -----------------------------------------------------------------------------
#   Interface class
# -----------------------------------------------------------------------------

class interfaceObj(object):
    _attr_list = ('ipv4', 'ipv6', 'mask', 'mac')
    _flag_list = ('BROADCAST', 'MULTICAST', 'UP', 'RUNNING', 'LOOPBACK', 'DYNAMIC',
                  'PROMISC', 'NOARP', 'POINTOPOINT', 'SIMPLEX', 'SMART', 'MASTER',
                  'SLAVE')

    def __init__(self, name, data):
        self._data = data
        self.name = name

        # properties
        self._ipv4 = None
        self._ipv6 = None
        self._mask = None
        self._mac = None

        self._dict = None

    @property
    def ipv4(self):
        if self._ipv4 == None:
            self._ipv4 = self._parseIpv4()
            log.debug("Parsed ipv4 is: {0}".format(self._ipv4))
        return self._ipv4

    @property
    def ipv6(self):
        if self._ipv6 == None:
            self._ipv6 = self._parseIpv6()
            log.debug("Parsed ipv6 is: {0}".format(self._ipv6))
        return self._ipv6

    @property
    def mask(self):
        if self._mask == None:
            self._mask = self._parseMask()
            log.debug("Parsed mask is: {0}".format(self._mask))
        return self._mask

    @property
    def mac(self):
        if self._mac == None:
            self._mac = self._parseMac()
            log.debug("Parsed mac is: {0}".format(self._mac))
        return self._mac

    def _parseIpv4(self):
        match = re.search(r'inet addr:([\d.]*)', self._data, flags=re.M | re.I)
        if match == None:
            return ''
        return match.group(1)

    def _parseIpv6(self):
        match = re.search(r'inet6 addr: ([\w:/]*)', self._data, flags=re.M | re.I)
        if match == None:
            return ''
        return match.group(1)

    def _parseMac(self):
        match = re.search(r'HWaddr ([\w:]*)', self._data, flags=re.M | re.I)
        if match == None:
            return ''
        return match.group(1)

    def _parseMask(self):
        match = re.search(r'Mask:([\d.]*)', self._data, flags=re.M | re.I)
        if match == None:
            return ''
        return match.group(1)

    # Returns a dictionary format of the parsed data
    def get_dict(self):
        return {'ipv4': self.ipv4,
                'ipv6': self.ipv6,
                'mac': self.mac,
                'mask': self.mask}

    def print_data_chunk(self):
        print(self._data)

# -----------------------------------------------------------------------------
#   Main Class: Parser Object
# -----------------------------------------------------------------------------

class parser(object):
    def __init__(self, content):
        self.text = content
        self._interfaces = None
        self._values = {}

    @property
    def interfaces(self):
        if self._interfaces == None:
            self._interfaces = self._parseInterface()
            log.debug("Parsed interfaces are: {0}".format(self.interfaces))
        return self._interfaces

    def get_interface(self, interface):
        if interface not in self._interfaces:
            raise InterfaceDoesNotExist
        # construct interface class
        data = None
        for data_block in self._parseText():
            if interface in data_block:
                data = data_block
        if data == None:
            raise InterfaceParseError
        return interfaceObj(interface, data)

    def _parseInterface(self):
        match = re.findall(r'^\w+', self.text, flags=re.M | re.I)
        return match

    def _parseText(self):
        paragraphs = self.text.split('\n\n')
        return paragraphs

    def get_values(self):
        if not self._values:
            for interfaceName in self._interfaces:
                interfaceObj = self.get_interface(interfaceName)
                self._values[interfaceName] = interfaceObj.get_dict()
        return self._values

if __name__ == '__main__':
    test = parser(test_text)
    interfaces = test.interfaces
    eth = test.get_interface('bond0')
    eth.ipv4
    eth.ipv6
    eth.mask
    eth.mac
    print(eth.get_dict())
    print(test.get_values())
