from mininet.cli import CLI
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import Node
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



class NatTopo(Topo):
    "Topology of private netowork with NAT' connected to public network"

    def build(self, **_opts):
        # Define Router
        router1 = self.addHost('rtr1', ip="10.69.0.1/24", mac="00:00:00:00:00:11", cls=LinuxRouter,
                               defaultRoute='via 10.69.0.2')  # Between networks 0 and 1

        # Define hosts with addresses and default routes
        my_host1 = self.addHost('myhost1', ip="192.168.1.101/24",
                               defaultRoute='via 192.168.1.1')

        my_host2 = self.addHost('myhost2', ip="192.168.1.102/24",
                               defaultRoute='via 192.168.1.1')

        nat = self.addHost('nat', ip="192.168.1.1/24")

        responder1 = self.addHost('responder1', ip="10.69.1.100/24",
                                  defaultRoute='via 10.69.1.1')


        # Switches for networks 0,1,2
        s0 = self.addSwitch('s0')
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')


        # links between switches to hosts
        self.addLink(s0, my_host1, cls=TCLink)
        self.addLink(s0, my_host2, cls=TCLink)
        self.addLink(s0, nat, cls=TCLink)
        self.addLink(s2, responder1, cls=TCLink)


        # Links between the switches and the routers
        self.addLink(nat, router1, intfName1='nat-eth1',
                     params1={'ip': '10.69.0.100/24'},
                     intfName2='r01-eth1',
                     params2={'ip': '10.69.0.1/24'})

        self.addLink(s2, router1, intfName2='r01-eth2',
                     params2={'ip': '10.69.1.1/24'})



topo = NatTopo()

net = Mininet( topo=topo)
net.start()

# in router 1, add route to private network
net['rtr1'].cmd('ip route add 192.168.1.0/24 via 10.69.0.100')

# In the NAT host, add default route
net['nat'].cmd('ip route add default via 10.69.0.1')

# In the responder, start a simple HTTP server
net['responder1'].cmd('python3 -m http.server 80&')
# Set the NAT not to send RST
net['nat'].cmd('iptables -A OUTPUT -p tcp --tcp-flags RST RST -j DROP')
CLI( net )
net.stop()
