import wishful_framework as wishful_module
from wishful_module_gitar.lib_sensor import SensorNodeFactory


__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2016, Universiteit Gent, IBCN, iMinds"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@intec.ugent.be"


@wishful_module.build_module
class GitarEngine(wishful_module.AgentModule):

    def __init__(self, **kwargs):
        super(GitarEngine, self).__init__()
        self.node_factory = SensorNodeFactory()
        self.supported_interfaces = kwargs["SupportedInterfaces"]
        self.node_factory.create_nodes_auto()
