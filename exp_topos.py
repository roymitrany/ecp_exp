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


class ExpTopo(Topo):
    def __init__(self):

        # super should be called only after class member initialization.
        # The super constructor calls build.
        super(ExpTopo, self).__init__()

    def build(self, **_opts):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        self.student_desktop = self.addHost('sd')
        self.close_responder = self.addHost('cr')
        self.remote_responder = self.addHost('rr')
        self.addLink(s1, s2, cls = TCLink, bw=1, delay='250ms',max_queue_size=100)
        self.addLink(s1, self.student_desktop, cls = TCLink)
        self.addLink(s1, self.close_responder, cls = TCLink)
        self.addLink(s2, self.remote_responder,cls = TCLink)

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


topos = { 'expTopo':ExpTopo, 'introTopo':IntroTopo }
