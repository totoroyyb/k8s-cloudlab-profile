"""Create single/multiple inter-connected node with 10.10.1.x ip addresses

Instructions:
Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the topology, and choosing the `shell` menu option.
Use `sudo` to run root commands. 
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context, needed to defined parameters
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

# Variable number of nodes.
pc.defineParameter("nodeCount", "Number of Nodes", portal.ParameterType.INTEGER, 1,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

# Pick your OS.
imageList = [
    ('default', 'Default Image'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'UBUNTU 22.04'),
    ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD', 'UBUNTU 20.04')]

pc.defineParameter("osImage", "Select OS image",
                   portal.ParameterType.IMAGE,
                   imageList[0], imageList,
                   longDescription="Pick a image...")

# Optional physical type for all nodes.
pc.defineParameter("phystype",  "Optional physical node type",
                   portal.ParameterType.STRING, "",
                   longDescription="Specify a single physical node type (pc3000,d710,etc) " +
                   "instead of letting the resource mapper choose for you.")

# Optionally create XEN VMs instead of allocating bare metal nodes.
# pc.defineParameter("useVMs",  "Use XEN VMs",
#                    portal.ParameterType.BOOLEAN, False,
#                    longDescription="Create XEN VMs instead of allocating bare metal nodes.")

# Optionally start X11 VNC server.
pc.defineParameter("startVNC",  "Start X11 VNC on your nodes",
                   portal.ParameterType.BOOLEAN, False,
                   longDescription="Start X11 VNC server on your nodes. There will be " +
                   "a menu option in the node context menu to start a browser based VNC " +
                   "client. Works really well, give it a try!")

# Optional link speed, normally the resource mapper will choose for you based on node availability
pc.defineParameter("linkSpeed", "Link Speed",portal.ParameterType.INTEGER, 0,
                   [(0,"Any"),(100000,"100Mb/s"),(1000000,"1Gb/s"),(10000000,"10Gb/s"),(25000000,"25Gb/s"),(100000000,"100Gb/s")],
                   advanced=True,
                   longDescription="A specific link speed to use for your lan. Normally the resource " +
                   "mapper will choose for you based on node availability and the optional physical type.")
                   
# For very large lans you might to tell the resource mapper to override the bandwidth constraints
# and treat it a "best-effort"
# pc.defineParameter("bestEffort",  "Best Effort", portal.ParameterType.BOOLEAN, False,
#                     advanced=True,
#                     longDescription="For very large lans, you might get an error saying 'not enough bandwidth.' " +
#                     "This options tells the resource mapper to ignore bandwidth and assume you know what you " +
#                     "are doing, just give me the lan I ask for (if enough nodes are available).")
                    
# Sometimes you want all of nodes on the same switch, Note that this option can make it impossible
# for your experiment to map.
pc.defineParameter("sameSwitch",  "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="Sometimes you want all the nodes connected to the same switch. " +
                    "This option will ask the resource mapper to do that, although it might make " +
                    "it impossible to find a solution. Do not use this unless you are sure you need it!")

# Retrieve the values the user specifies during instantiation.
params = pc.bindParameters()

# Check parameter validity.
if params.nodeCount < 1:
    pc.reportError(portal.ParameterError("You must choose at least 1 node.", ["nodeCount"]))

if params.phystype != "":
    tokens = params.phystype.split(",")
    if len(tokens) != 1:
        pc.reportError(portal.ParameterError("Only a single type is allowed", ["phystype"]))

pc.verifyParameters()

# Create link.
if params.nodeCount > 1:
    lan = request.Link()
    # if params.nodeCount == 2:
    #     lan = request.Link()
    # else:
    #     lan = request.LAN()
    
    if params.linkSpeed > 0:
        lan.bandwidth = params.linkSpeed
    if params.sameSwitch:
        lan.setNoInterSwitchLinks()
    

# Process nodes, adding to link.
for i in range(params.nodeCount):
    # Create a node and add it to the request
    name = "node" + str(i)
    node = request.RawPC(name)
    node.routable_control_ip = True

    if params.osImage and params.osImage != "default":
        node.disk_image = params.osImage
    
    # Add to lan
    if params.nodeCount > 1:
        iface = node.addInterface("eth1", pg.IPv4Address('10.10.1.%d' % (i + 1),'255.255.255.0'))
        lan.addInterface(iface)

    # Optional hardware type.
    if params.phystype != "":
        node.hardware_type = params.phystype

    ### run setup scripts
    # install mount point && generate ssh keys
    node.addService(pg.Execute(shell="bash",
        command="/local/repository/ssh.sh > /tmp/ssh.log 2>&1"))
    node.addService(pg.Execute(shell="bash",
        command="/local/repository/mount.sh > /tmp/mount.log 2>&1"))

    # dependencies installation
    node.addService(pg.Execute(shell="bash",
        command="/local/repository/install-dependencies.sh > /tmp/dependencies.log 2>&1"))

    if i == 0:
        ''' Install the minikube for the main controller server (default to the first node)
        '''
        # docker installation
        node.addService(pg.Execute(shell="bash",
            command="/local/repository/install-kubectl.sh > /tmp/kubectl.log 2>&1"))

        # docker installation
        node.addService(pg.Execute(shell="bash",
            command="/local/repository/install-docker.sh > /tmp/docker.log 2>&1"))

        # minikube installation
        node.addService(pg.Execute(shell="bash",
            command="/local/repository/install-minikube.sh > /tmp/minikube.log 2>&1"))

    # increase number of open file descriptors
    node.addService(pg.Execute(shell="bash",
        command="/local/repository/ulimit.sh > /tmp/ulimit.log 2>&1"))
    
    # Install and start X11 VNC. Calling this informs the Portal that you want a VNC
    # option in the node context menu to create a browser VNC client.
    #
    # If you prefer to start the VNC server yourself (on port 5901) then add nostart=True. 
    #
    if params.startVNC:
        node.startVNC()
    

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)
