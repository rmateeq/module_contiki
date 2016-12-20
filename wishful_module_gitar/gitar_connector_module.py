import wishful_framework as wishful_module
from wishful_module_gitar.lib_sensor import SensorNodeFactory
from wishful_module_gitar.lib_gitar import ProtocolConnector
import logging
# import crc16


__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2016, Universiteit Gent, IBCN, iMinds"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@intec.ugent.be"


@wishful_module.build_module
class GitarEngine(wishful_module.AgentModule):

    def __init__(self, **kwargs):
        super(GitarEngine, self).__init__()
        self.log = logging.getLogger('GITAREngine.main')
        self.gitar_config = kwargs['GitarConfig']
        self.supported_interfaces = kwargs['SupportedInterfaces']
        # @TODO this should be dynamically build!!!
        self.protocol_attributes = kwargs['ControlAttributes']
        self.protocol_functions = kwargs['ControlFunctions']
        self.node_factory = SensorNodeFactory()
        self.node_factory.create_nodes(self.gitar_config, self.supported_interfaces)
        # self.connector = ProtocolConnector(crc16.crc16xmodem(str.encode("GITAR")), "GITAR")
        # self.connector = ProtocolConnector(0, "GITAR")

    @wishful_module.on_start()
    def start_gitar_engine(self):
        for iface in self.supported_interfaces:
            node = self.node_factory.get_node(iface)
            connector = ProtocolConnector(0, "GITAR")
            node.add_connector(connector)
            if type(self.protocol_attributes) == list:
                for attr_csv in self.protocol_attributes:
                    self.node_factory.parse_control_attributes(attr_csv, node, connector)
            else:
                self.node_factory.parse_control_attributes(self.protocol_attributes, node, connector)
            if type(self.protocol_functions) == list:
                for function_csv in self.protocol_functions:
                    self.node_factory.parse_control_functions(function_csv, node, connector)
            else:
                self.node_factory.parse_control_functions(self.protocol_functions, node, connector)
        pass

    @wishful_module.on_exit()
    def stop_gitar_engine(self):
        return

    @wishful_module.on_connected()
    def gitar_engine_connected(self):
        return

    @wishful_module.on_disconnected()
    def gitar_engine_disconnected(self):
        return

    @wishful_module.on_first_call_to_module()
    def gitar_engine_first_call(self):
        return
