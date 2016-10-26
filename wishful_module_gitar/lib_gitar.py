import configparser as ConfigParser
import logging
import csv
from wishful_module_gitar.contiki_node_custom import CustomNode
from wishful_module_gitar.contiki_node_rpc import RPCNode
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper
from communication_wrappers.coap_wrapper import CoAPWrapper


def ConfigSectionMap(config, section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        dict1[option] = config.get(section, option)
    return dict1


def singleton(cls):
    instance = cls()
    instance.__call__ = lambda: instance
    return instance


class SensorNodeFactory():

    class __SensorNodeFactory:

        def __init__(self):
            self.log = logging.getLogger('SensorNodeFactory')
            self.__nodes = {}

        def __str__(self):
            return repr(self) + self.val
    instance = None

    def __init__(self):
        if not SensorNodeFactory.instance:
            SensorNodeFactory.instance = SensorNodeFactory.__SensorNodeFactory()

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def create_nodes(self, config_file, supported_interfaces):
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read(config_file)
        self.log.info('Creating contiki instances %s', config.sections())

        """
        Create nodes
        """
        for interface in config.sections():
            if interface in supported_interfaces:

                node_id = int(config.get(interface, 'NodeID'))
                mac_addr = config.get(interface, 'MacAddress')
                ip_addr = config.get(interface, 'IpAddress')

                # Create a com_wrapper instance
                com_method = config.get(interface, 'CommunicationMethod')
                com_wrapper = None
                if com_method == 'ContikiSerialdump':
                    com_wrapper = SerialdumpWrapper(config.get(interface, 'SerialDev'), interface)
                elif com_method == 'CoAP':
                    com_wrapper = CoAPWrapper(ip_addr)
                else:
                    self.log.fatal('invalid CommunicationMethod')

                # Create a specific type of node
                node_type = config.get(interface, 'NodeType')
                if node_type == 'ContikiCustomNode':
                    self.__nodes[interface] = CustomNode(mac_addr, ip_addr, interface, com_wrapper)
                elif node_type == 'ContikiRPCNode':
                    self.__nodes[interface] = RPCNode(node_id, interface, mac_addr, ip_addr, com_wrapper)
                else:
                    self.log.fatal('invalid NodeType')

            else:
                self.log.info('Skipping interface %s', interface)

    def configure_datatypes(self, config_file):
        """
        Configure the datatypes for a specific node_type
        """

    def configure_connectors(self, config_file):
        """
        Configure the connectors for a specific node_type
        """

    def configure_parameters(self, config_file):
        """
        Configure the parameters for a specific connector
        """

    def configure_functions(self, config_file):
        """
        Configure the functions for a specific connector
        """

    def get_nodes(self):
        return self.__nodes

    def get_node(self, interface_name):
        return self.__nodes[interface_name]
