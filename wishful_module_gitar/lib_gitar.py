import abc
import configparser as ConfigParser
import logging
import csv
import struct

from wishful_module_gitar.contiki_node_custom import CustomNode
from wishful_module_gitar.contiki_node_rpc import RPCNode
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper
from communication_wrappers.coap_wrapper import CoAPWrapper


class SensorNode():
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def register_datatypes(self, datatype_defs):
        pass

    @abc.abstractmethod
    def register_connectors(self, con_defs):
        pass

    @abc.abstractmethod
    def register_parameters(self, connector_module, param_defs):
        pass

    @abc.abstractmethod
    def register_functions(self, connector_module, func_defs):
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


class SensorDataType():

    def __init__(self, uid=0, name="", size=0, struct_format="", endianness="<"):
        self.uid = uid
        self.name = name
        self.size = size
        self.struct_format = struct_format
        self.endianness = endianness
        self.struct = None

        # No Variable length in struct_format. Save the struct for better preformance
        if "%" not in self.struct_format:
            self.struct = struct.Struct(self.endianness + self.struct_format)

    def to_bin(self, value, length=0):
        if self.struct is not None:
            return self.struct.pack(value)
        else:
            fmt = self.struct_format % length
            return struct.pack(self.endianness + fmt, value)

    def from_bin(self, buf, length=0):
        if self.struct is not None:
            return self.struct.unpack_from(buf)
        else:
            fmt = self.struct_format % length
            return struct.unpack_from(self.endianness + fmt, buf)

    def has_variable_size(self):
        if self.size == 0:
            return True
        else:
            return False


class SensorParameter():

    def __init__(self, uid=0, name="", datatype=None):
        self.uid = uid
        self.name = name
        self.datatype = datatype

    def has_variable_size(self):
        return self.datatype.has_variable_size()


class SensorFunction():

    def __init__(self, uid=0, name="", args_datatypes=None, ret_datatype=None):
        self.uid = uid
        self.name = name

        if args_datatypes is None:
            self.args_datatypes = []
        else:
            self.args_datatypes = args_datatypes

        self.ret_datatype = ret_datatype

    def num_of_args(self):
        return len(self.args_datatypes)


class SensorConnector():

    def __init__(self, uid, name="", paramsIDs=None, params=None, funcsIDs=None, funcs=None):
        self.uid = uid
        self.name = name

        if paramsIDs is None:
            self.paramsIDs = {}
        else:
            self.paramsIDs = paramsIDs
        if params is None:
            self.params = []
        else:
            self.params = params
           
        if funcsIDs is None:
            self.funcsIDs = {}
        else:
            self.funcsIDs = funcsIDs
        if funcs is None:
            self.funcs = []
        else:
            self.funcs = funcs

    def add_parameter(self, param):
        if param.name in self.paramsIDs:
            return False
        self.paramsIDs[param.name] = param.uid
        self.params[param.uid] = param
        return True

    def num_of_parameters(self):
        return len(self.params)

    def get_parameter_uid(self, name):
        return self.paramsIDs[name]

    def get_parameter(self, name):
        return self.params[self.paramsIDs[name]]
        
    def add_function(self, func):
        if func.name in self.funcsIDs:
            return False
        self.funcsIDs[func.name] = func.uid
        self.funcs[func.uid] = func
        return True

    def num_of_functions(self):
        return len(self.funcs)

    def get_function_uid(self, name):
        return self.funcsIDs[name]

    def get_function(self, name):
        return self.funcs[self.funcsIDs[name]]


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

    def configure_datatypes(self, datatype_config):
        for node_type in datatype_config.keys():
            try:
                file_rp = open(datatype_config[node_type], 'rt')
                reader = csv.DictReader(file_rp)
                datatype_defs = []
                for row in reader:
                    r_def = {
                        'unique_id': row["unique_id"],
                        'unique_name': row["unique_name"],
                        'size': row["size"],
                        'format': row["format"],
                        'endianness': row["endianness"]
                    }
                    datatype_defs.append(r_def)

                for interface in self.__nodes.keys():
                    self.__nodes[interface].register_datatypes(datatype_defs)

            except Exception as e:
                self.log.fatal("Could not read datatypes for %s, from %s error: %s" % (node_type, datatype_config[node_type], e))

    def configure_connectors(self, connector_config):
        for node_type in connector_config.keys():
            try:
                file_rp = open(connector_config[node_type], 'rt')
                reader = csv.DictReader(file_rp)
                con_defs = []
                for row in reader:
                    r_def = {
                        'unique_id': row["unique_id"],
                        'unique_name': row["unique_name"],
                    }
                    con_defs.append(r_def)

                for interface in self.__nodes.keys():
                    self.__nodes[interface].register_datatypes(con_defs)

            except Exception as e:
                self.log.fatal("Could not read datatypes for %s, from %s error: %s" % (node_type, connector_config[node_type], e))

    def configure_parameters(self, parameter_config):
        for connector_module in parameter_config.keys():
            try:
                file_rp = open(parameter_config[connector_module], 'rt')
                reader = csv.DictReader(file_rp)
                param_defs = []
                for row in reader:
                    r_def = {
                        'unique_id': row["unique_id"],
                        'unique_name': row["unique_name"],
                        'datatype': row["datatype"],
                    }
                    param_defs.append(r_def)

                for interface in self.__nodes.keys():
                    self.__nodes[interface].register_parameters(connector_module, param_defs)

            except Exception as e:
                self.log.fatal("Could not read parameters for %s, from %s error: %s" % (connector_module, parameter_config[connector_module], e))

    def configure_functions(self, function_config):
        for connector_module in function_config.keys():
            try:
                file_rp = open(function_config[connector_module], 'rt')
                reader = csv.DictReader(file_rp)
                func_defs = []
                for row in reader:
                    r_def = {
                        'unique_id': row["unique_id"],
                        'unique_name': row["unique_name"],
                        'args_datatypes': row["args_datatypes"],
                        'ret_datatype': row["ret_datatype"],
                    }
                    func_defs.append(r_def)

                for interface in self.__nodes.keys():
                    self.__nodes[interface].register_parameters(connector_module, func_defs)

            except Exception as e:
                self.log.fatal("Could not read parameters for %s, from %s error: %s" % (connector_module, function_config[connector_module], e))

    def get_nodes(self):
        return self.__nodes

    def get_node(self, interface_name):
        return self.__nodes[interface_name]
