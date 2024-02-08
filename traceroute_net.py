from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Node, OVSController
from mininet.topo import Topo


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


class TraceRouteTopo(Topo):
    "Topology for meeting 2 TCP protocol analysis"
    router_list = []

    def build(self, **_opts):
        # Define Routers
        router1 = self.addHost('rtr1', ip="10.69.0.1/24", mac="00:00:00:00:00:11", cls=LinuxRouter,
                               defaultRoute='via 10.69.1.2')  # Between networks 0 and 1
        router2 = self.addHost('rtr2', ip="10.69.1.2/24", mac="00:00:00:00:00:22", cls=LinuxRouter,
                               defaultRoute='via 10.69.2.3')  # Between networks 0 and 2

        router3 = self.addHost('rtr3', ip="10.69.2.3/24", mac="00:00:00:00:00:33", cls=LinuxRouter,
                               defaultRoute='via 10.69.2.2')  # Between networks 0 and 2

        # Define hosts with addresses and default routes
        my_host = self.addHost('myhost', ip="10.69.0.100/24",
                               defaultRoute='via 10.69.0.1')

        responder = self.addHost('responder', ip="10.69.3.100/24",
                                 defaultRoute='via 10.69.3.3')

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

        # Network 2
        self.addLink(s2, router2, cls=TCLink, intfName2='r02-eth2',
                     params2={'ip': '10.69.2.2/24'}, delay='125ms')
        self.addLink(s2, router3, cls=TCLink)

        # Network 3
        self.addLink(s3, router3, cls=TCLink, intfName2='r03-eth2',
                     params2={'ip': '10.69.3.3/24'}, delay='125ms')
        self.addLink(s3, responder, cls=TCLink)


topo = TraceRouteTopo()

net = Mininet(topo=topo, controller=OVSController)
net.start()

# add route to myhost network in router 2, router3 and responder
net['rtr2'].cmd('ip route add 10.69.0.0/24 via 10.69.1.1')
net['rtr3'].cmd('ip route add 10.69.0.0/24 via 10.69.2.2')
net['responder'].cmd('ip route add 10.69.0.0/24 via 10.69.2.2')

CLI(net)
net.stop()
