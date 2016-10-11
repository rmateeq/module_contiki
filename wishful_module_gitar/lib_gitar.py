import abc
import configparser as ConfigParser
import logging
import csv

from wishful_module_gitar.contiki_node_custom import CustomNode
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper

class SensorNode():
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def register_parameters(self, connector_module, param_defs):
        pass

    @abc.abstractmethod
    def write_parameters(self, connector_module, param_key_values):
        pass

    @abc.abstractmethod
    def read_parameters(self, connector_module, param_keys):
        pass

    @abc.abstractmethod
    def register_measurements(self, connector_module, measurement_defs):
        pass

    @abc.abstractmethod
    def read_measurements(self, connector_module, measurement_keys):
        pass

    @abc.abstractmethod
    def register_events(self, connector_module, event_defs):
        pass

    @abc.abstractmethod
    def add_events_subscriber(self, connector_module, event_names, event_callback):
        pass

    @abc.abstractmethod
    def reset(self):
        pass


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

    def create_nodes(self, config_file, supported_interfaces, control_extensions):
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read(config_file)
        self.log.info('Creating contiki instances %s', config.sections())
        for interface in config.sections():
            if interface in supported_interfaces:
                mac_addr = config.get(interface, 'MacAddress')
                ip_addr = config.get(interface, 'IpAddress')
                communication_wrapper = config.get(interface, 'CommunicationWrapper')
                communication_wrapper_obj = None
                if communication_wrapper == 'ContikiSerialdump':
                    communication_wrapper_obj = SerialdumpWrapper(config.get(interface, 'SerialDev'), interface)
                else:
                    self.log.fatal('invalid communication wrapper')
                self.__nodes[interface] = CustomNode(mac_addr, ip_addr, interface, communication_wrapper_obj)
            else:
                self.log.info('Skipping interface %s', section)

        for connector_module in control_extensions.keys():
            try:
                file_rp = open(control_extensions[connector_module], 'rt')
                reader = csv.DictReader(file_rp)
                param_defs = []
                measurement_defs = []
                event_defs = []
                for row in reader:
                    r_def = {'unique_name': row["unique_name"], 'unique_id': row["unique_id"], 'type_name': row[
                        "type"], 'type_len': row["length"], 'type_format': row["struct_format"], 'type_subformat': row["struct_subformat"]}
                    if row['category'] == "PARAMETER":
                        param_defs.append(r_def)
                    elif row['category'] == "MEASUREMENT":
                        measurement_defs.append(r_def)
                    elif row['category'] == "EVENT":
                        event_defs.append(r_def)
                    else:
                        self.log.info("Illegal parameter category: %s" % row['category'])

                for iface in self.__nodes.keys():
                    self.__nodes[iface].register_parameters(connector_module, param_defs)
                    self.__nodes[iface].register_measurements(connector_module, measurement_defs)
                    self.__nodes[iface].register_events(connector_module, event_defs)

            except Exception as e:
                self.log.fatal("Could not read parameters for %s, from %s error: %s" %
                               (connector_module, control_extensions[connector_module], e))

    def get_nodes(self):
        return self.__nodes

    def get_node(self, interface_name):
        return self.__nodes[interface_name]
