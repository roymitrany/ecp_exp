"""TCP/IP experiment topology
There are 3 hosts in the network.

Student Desktop - that's the host from which the student perform all their tests
Close Responder - a responde with low latency and high throughput towards the exp host
Remote Responder - a respondes which has high latency and low bandwidth towards the host


Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""
from mininet.link import TCLink
from mininet.topo import Topo
from mininet.node import Node
import random

"""*************************************************************
                     Hosts
****************************************************************"""


# This type of host has routing capabilities

class LinuxRouter(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        # Enable forwarding on the router
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


# This type of host runs iperf3 server

class IperfResponder(Node):
    "A Node listening as iperf3 server."

    def config(self, **params):
        super(IperfResponder, self).config(**params)

        self.cmd('sysctl net.ipv4.tcp_rmem="400000 400000 400000"')  # Avoid RWin scale (confuses Wireshark)
        self.cmd('sysctl net.ipv4.neigh.{}-eth0.gc_stale_time=720000'.format(self.name))
        self.cmd('ip neighbor add 10.60.0.100 lladdr 00:00:00:00:01:00 nud permanent')  # Static arp cache from responder to sender
        self.cmd('ethtool -K {}-eth0 tso off'.format(self.name))  # Disable GSO/TSO
        self.cmd('ethtool -K {}-eth0 gso off'.format(self.name))
        self.cmd('iperf3 -s&')

    def set_sack(self, sack_val):
        self.cmd('sysctl net.ipv4.tcp_sack={}'.format(sack_val))


class IperfClient(Node):

    def config(self, **params):
        super(IperfClient, self).config(**params)

        self.cmd('sysctl net.ipv4.neigh.{}-eth0.gc_stale_time=720000'.format(self.name))  # Extend ARP cache expiration
        self.cmd('ethtool -K {}-eth0 tso off'.format(self.name))  # Disable GSO/TSO
        self.cmd('ethtool -K {}-eth0 gso off'.format(self.name))


class PingerNode(Node):
    "A Node with IP forwarding enabled."

    def config(self, **params):
        super(PingerNode, self).config(**params)

        self.cmd('python3 random_pinger.py 10.69.0 1 20&')

    def terminate(self):
        super(PingerNode, self).terminate()


"""*************************************************************
                     Topologies
****************************************************************"""


class IntroTopo(Topo):
    def build(self, **_opts):
        s1 = self.addSwitch('s1')
        my_host = self.addHost('myhost',ip="10.69.0.100/24")
        close_dst = self.addHost('dst1',ip="10.69.0.1/24")
        far_dst = self.addHost('dst2',ip="10.69.0.2/24")
        lossy_dst = self.addHost('dst3',ip="10.69.0.3/24")

        self.addLink(s1, my_host, cls=TCLink)
        self.addLink(s1, close_dst, cls=TCLink, bw=1, delay='2ms')
        self.addLink(s1, far_dst,cls=TCLink, bw=1, delay='250ms')
        self.addLink(s1, lossy_dst,cls=TCLink, bw=1, loss=50)



class ArpTopo(Topo):
    def build(self, **_opts):
        s1 = self.addSwitch('s1')
        my_host = self.addHost('myhost', ip="10.69.0.100/24")
        self.addLink(s1, my_host, cls=TCLink)

        for i in range(1, 21):
            dst = self.addHost('dst%d' % i, cls=PingerNode, ip="10.69.0.%d/24" % i)
            self.addLink(s1, dst, cls=TCLink)


class RedirectTopo(Topo):
    "Topology with 2 routers and 3 subnets"

    def build(self, **_opts):
        # Define Routers
        router1 = self.addHost('rtr1', ip="10.69.0.1/24", mac="00:00:00:00:00:11", cls=LinuxRouter,
                               defaultRoute='via 10.69.0.2')  # Between networks 0 and 1
        router2 = self.addHost('rtr2', ip="10.69.0.2/24", mac="00:00:00:00:00:22", cls=LinuxRouter,
                               defaultRoute='via 10.69.0.1')  # Between networks 0 and 2

        # Define hosts with addresses and default routes
        my_host = self.addHost('myhost', ip="10.69.0.100/24",
                               defaultRoute='via 10.69.0.1')

        responder1 = self.addHost('responder1', ip="10.69.1.100/24",
                                  defaultRoute='via 10.69.1.1')

        responder2 = self.addHost('responder2', ip="10.69.2.100/24",
                                  defaultRoute='via 10.69.2.2')

        # Switches for networks 0,1,2
        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # links between switches to hosts
        self.addLink(s0, my_host, cls=TCLink)
        self.addLink(s1, responder1, cls=TCLink)
        self.addLink(s2, responder2, cls=TCLink)

        # Links between the switches and the routers
        self.addLink(s0, router1, intfName2='r01-eth1',
                     params2={'ip': '10.69.0.1/24'})

        self.addLink(s1, router1, intfName2='r01-eth2',
                     params2={'ip': '10.69.1.1/24'})

        self.addLink(s0, router2, intfName2='r02-eth1',
                     params2={'ip': '10.69.0.2/24'})

        self.addLink(s2, router2, intfName2='r02-eth2',
                     params2={'ip': '10.69.2.2/24'})


class TcpTopo(Topo):
    "Topology for meeting 2 TCP protocol analysis"

    def build(self, qSize=None, delay=None, **_opts):
        # Queue size 0 parameter means None
        qSize = None if qSize == 0 else qSize

        delay = str(delay) + 'ms' if delay else None
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        my_host = self.addHost('myhost', ip="10.69.0.100/24", mac="00:00:00:00:01:00",
                               cls=IperfClient)
        close_responder = self.addHost('resp1', ip="10.69.0.1/24", cls=IperfResponder)
        remote_responder = self.addHost('resp2', ip="10.69.0.2/24", cls=IperfResponder)

        self.addLink(s1, s2, cls=TCLink, bw=0.5, delay=delay, max_queue_size=qSize, use_tbf=True)
        self.addLink(s1, my_host, cls=TCLink)
        self.addLink(s1, close_responder, cls=TCLink)
        self.addLink(s2, remote_responder, cls=TCLink)

class TraceRouteTopo(Topo):
    "Topology for meeting 2 TCP protocol analysis"
    router_list = []
    def build(self, **_opts):
        # Define Routers
        #router_list[i] = self.addHost('rtr%d'%i, ip="10.69.%d.1/24", mac="00:00:00:00:00:%d%d"%(i,i), cls=LinuxRouter,
        #                       defaultRoute='via 10.69.0.2')  # Between networks 0 and 1
        router1 = self.addHost('rtr1', ip="10.69.0.1/24", mac="00:00:00:00:00:11", cls=LinuxRouter,
                               defaultRoute='via 10.69.1.2')  # Between networks 0 and 1
        router2 = self.addHost('rtr2', ip="10.69.1.2/24", mac="00:00:00:00:00:22", cls=LinuxRouter,
                               defaultRoute='via 10.69.2.2')  # Between networks 0 and 2
        router3 = self.addHost('rtr3', ip="10.69.2.3/24", mac="00:00:00:00:00:33", cls=LinuxRouter,
                               defaultRoute='via 10.69.2.2')  # Between networks 0 and 2

        # Define hosts with addresses and default routes
        my_host = self.addHost('myhost', ip="10.69.0.100/24",
                               defaultRoute='via 10.69.0.1')


        responder = self.addHost('responder2', ip="10.69.2.100/24",
                                  defaultRoute='via 10.69.2.2')

        # Switches for networks 0,1,2
        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Network 0
        self.addLink(s0, my_host, cls=TCLink)
        self.addLink(s0, router1, cls=TCLink)

        # Network 1
        self.addLink(s1, router1, cls=TCLink, intfName2='r01-eth2',
                     params2={'ip': '10.69.1.1/24'}, delay='250ms')
        self.addLink(s1, router2, cls=TCLink)
        #router2.setHostRoute('10.69.0.0/24', '10.69.1.1')

        # Network 2
        self.addLink(s2, router2, cls=TCLink, intfName2='r02-eth2',
                     params2={'ip': '10.69.2.2/24'}, delay='125ms')

        # links between switches to hosts
        self.addLink(s2, responder, cls=TCLink)


topos = {'introTopo': IntroTopo, 'arpTopo': ArpTopo, 'redirectTopo': RedirectTopo, 'tcpTopo': TcpTopo,
         'traceRouteTopo':TraceRouteTopo}
