"""
Your awesome Distance Vector router for CS 168
"""

import sim.api as api
import sim.basics as basics

# We define infinity as a distance of 16.
INFINITY = 16


class DVRouter (basics.DVRouterBase):
  #NO_LOG = True # Set to True on an instance to disable its logging
  # POISON_MODE = True # Can override POISON_MODE here
  # DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

  def __init__ (self):
    self.portLatency = dict()
    self.routeTableLatency = dict()
    self.routeTablePort = dict()
    self.routeTableTime = dict()
    self.neighborHosts = dict()

    """
    Called when the instance is initialized.

    You probably want to do some additional initialization here.
    """
    self.start_timer() # Starts calling handle_timer() at correct rate

  def handle_link_up (self, port, latency):
    """
    Called by the framework when a link attached to this Entity goes up.

    The port attached to the link and the link latency are passed in.
    """
    self.portLatency[port] = latency
    for d in self.routeTableLatency:
      self.send(basics.RoutePacket(d, self.routeTableLatency[d]) , port , False)
  
  def handle_link_down (self, port):
    """
    Called by the framework when a link attached to this Entity does down.

    The port number used by the link is passed in.
    """
    # self.log(" %s (%s)", port, api.current_time())
    to_delete = []

    del self.portLatency[port]

    for d in self.neighborHosts.keys():
      if self.neighborHosts[d][1] == port:
        del self.neighborHosts[d]

    for d in self.routeTablePort:
      if self.routeTablePort[d] == port:
        if d in self.neighborHosts:
          self.routeTableLatency[d] = self.neighborHosts[d][0]
          self.routeTablePort[d] = self.neighborHosts[d][1]
          self.routeTableTime[d] = api.current_time()
          self.send(basics.RoutePacket(d, self.routeTableLatency[d]) , port , True)
        else:
          to_delete.append(d)
          self.sendPoison(port , d)
    self.delete(to_delete)

  def shouldUpdate(self , packet , port):
    if packet.destination not in self.routeTableLatency: return True
    if self.routeTablePort[packet.destination] == port: return True
    if self.portLatency[port] + packet.latency < self.routeTableLatency[packet.destination]: return True
    return False
  
  def delete(self , to_delete):
    for dest in to_delete:
      del self.routeTableLatency[dest]
      del self.routeTablePort[dest]
      del self.routeTableTime[dest]
 
  def handleRoutePacket(self , packet , port):
    # print("shemowmebamde" , self.name , packet , packet.src)
    if not self.shouldUpdate(packet , port): return
    # print("shemomwbis mere" , self.name , packet)
    self.routeTableLatency[packet.destination] = packet.latency + self.portLatency[port]
    self.routeTableTime[packet.destination] = api.current_time()
    self.routeTablePort[packet.destination] = port
    if packet.destination in self.neighborHosts and self.neighborHosts[packet.destination][0] < self.routeTableLatency[packet.destination]:
      self.routeTableLatency[packet.destination] = self.neighborHosts[packet.destination][0]
      self.routeTableTime[packet.destination] = api.current_time()
      self.routeTablePort[packet.destination] = self.neighborHosts[packet.destination][1]

    routePacket = basics.RoutePacket(packet.destination , self.routeTableLatency[packet.destination])
    self.send(routePacket, port, flood = True)
  
  def handleHostDiscoveryPacket(self , packet , port):
    # print(self.name , packet.src , self.portLatency[port])
    self.neighborHosts[packet.src] = (self.portLatency[port] , port)
    if packet.src not in self.routeTableLatency or self.portLatency[port] < self.routeTableLatency[packet.src]:
      self.routeTableLatency[packet.src] = self.portLatency[port]
      self.routeTablePort[packet.src] = port
      self.routeTableTime[packet.src] = api.current_time()

  def sendPoison(self , port , dest):
    routePacket = basics.RoutePacket(dest , INFINITY)
    self.send(routePacket , port , True)

  def handle_rx (self, packet, port):
    """
    Called by the framework when this Entity receives a packet.

    packet is a Packet (or subclass).
    port is the port number it arrived on.

    You definitely want to fill this in.
    """
    if isinstance(packet, basics.RoutePacket):
      self.handleRoutePacket(packet , port)
    elif isinstance(packet, basics.HostDiscoveryPacket):
      self.handleHostDiscoveryPacket(packet , port)
    else:
      if packet.dst in self.routeTableLatency and self.routeTableLatency[packet.dst] < INFINITY: 
        if port != self.routeTablePort[packet.dst]: 
          self.send(packet, self.routeTablePort[packet.dst])

  def handle_timer (self):
    """
    Called periodically.

    When called, your router should send tables to neighbors.  It also might
    not be a bad place to check for whether any entries have expired.
    """
    to_delete = []
    for dest in self.routeTableLatency:
      if api.current_time() - self.routeTableTime[dest] <= 15:
        routePacket = basics.RoutePacket(dest , self.routeTableLatency[dest])
        self.send(routePacket , self.routeTablePort[dest] , True)
      else:
        if dest in self.neighborHosts and self.neighborHosts[dest][1] == self.routeTablePort[dest]:
          self.routeTableLatency[dest] = self.neighborHosts[dest][0]
          self.routeTablePort[dest] = self.neighborHosts[dest][1]
          self.routeTableTime[dest] = api.current_time()
          routePacket = basics.RoutePacket(dest , self.routeTableLatency[dest])
          self.send(routePacket , self.routeTablePort[dest] , True)
        else:
          to_delete.append(dest)
          routePacket = basics.RoutePacket(dest , INFINITY)
          self.send(routePacket , self.routeTablePort[dest] , True)
    
    self.delete(to_delete)