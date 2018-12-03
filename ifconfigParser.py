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

# -----------------------------------------------------------------------------
#   Main Class: Parser Object
# -----------------------------------------------------------------------------

class parser(object):
    _attr_list = ('ipv4', 'ipv6', 'mask', 'mac')
    _flag_list = ('BROADCAST', 'MULTICAST', 'UP', 'RUNNING', 'LOOPBACK', 'DYNAMIC',
                  'PROMISC', 'NOARP', 'POINTOPOINT', 'SIMPLEX', 'SMART', 'MASTER',
                  'SLAVE')

    def __init__(self, content):
        self.text = content
        self.interfaces = None

    def get_interfaces(self):
        if self.interfaces == None:
            self.interfaces = self._parseInterface()
        log.debug("Parsed interfaces are: {0}".format(self.interfaces))

    def _parseIpv4(self):
        match = re.findall(r'inet addr:\d*.\d*.\d*.\d*', self.text, flags=re.M | re.I)
        print(match)

    def _parseInterface(self):
        match = re.findall(r'^\w+', self.text, flags=re.M | re.I)
        return match

if __name__ == '__main__':
    test = parser(test_text)
    test.get_interfaces()
    test._parseIpv4()
