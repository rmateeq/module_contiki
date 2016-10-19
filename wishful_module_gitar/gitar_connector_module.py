__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2016, Universiteit Gent, IBCN, iMinds"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@intec.ugent.be"

import wishful_framework as wishful_module
from wishful_module_gitar.lib_gitar import SensorNodeFactory
import logging
import subprocess


@wishful_module.build_module
class GitarEngine(wishful_module.AgentModule):

    def __init__(self, **kwargs):
        super(GitarEngine, self).__init__()
        self.log = logging.getLogger('GITAREngine.main')
        self.node_factory = SensorNodeFactory()
        self.node_factory.create_nodes(kwargs['GitarConfig'], kwargs['SupportedInterfaces'], kwargs['ControlExtensions'])
        pass

    def create_control_net(self):
        for iface, node in self.node_factory.get_nodes.iteritems():
            node_id = node.node_id
            serial_dev = node.serial_dev
            control_prefix = "fdc" + str(node_id) + "::"
            control_tunslip_interface_id = "1"
            prefix_length = "/64"
            tunslip_ip_addr = control_prefix + control_tunslip_interface_id + prefix_length
            slip_process = subprocess.Popen(['sudo', '../communication_wrappers/bin/tunslip6', '-C', '-s'+serial_dev, tunslip_ip_addr],stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.slip_processes[iface] = slip_process
