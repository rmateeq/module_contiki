import configparser as ConfigParser
import logging
import abc
#from wishful_module_gitar.custom_node import CustomNode
#from wishful_module_gitar.rpc_node import RPCNode
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper
from communication_wrappers.coap_wrapper import CoAPWrapper


class SensorDataType():

    def __init__(self, uid=0, name="", size=0, endianness="<", fmt=""):
        self.log = logging.getLogger('SensorDataType.' + name)
        self.uid = uid
        self.name = name
        self.size = size
        self.endianness = endianness
        self.fmt = fmt

    @abc.abstractmethod
    def to_bytes(self, *args):
        """
        Transform value(s) to bytes specified by datatype format
        """
        pass

    @abc.abstractmethod
    def read_bytes(self, buf):
        """
        Read value(s) from a buffer. Returns a tuple according to the datatype format
        """
        pass


class Generic():

    def __init__(self, uid=0, name="", datatype=None):
        self.log = logging.getLogger()
        self.uid = uid
        self.name = name
        self.datatype = None

        if isinstance(datatype, SensorDataType):
            self.datatype = datatype
        else:
            self.log.fatal('invalid argument type')

    def set_datatype(self, datatype):
        if isinstance(datatype, SensorDataType):
            self.datatype = datatype
        else:
            self.log.fatal('invalid argument type')


class SensorParameter(Generic):

    def __init__(self, uid=0, name="", datatype=None):
        Generic.__init__(self, uid, name, datatype)
        self.change_list = []


class SensorEvent():

    def __init__(self, uid=0, name="", datatype=None):
        Generic.__init__(self, uid, name, datatype)
        self.event_duration = 0
        self.subscriber_callbacks = []


class SensorMeasurement():

    def __init__(self, uid=0, name="", datatype=None):
        Generic.__init__(self, uid, name, datatype)
        self.is_periodic = False
        self.read_interval = 0
        self.report_interval = 0
        self.num_iterations = 0
        self.report_callback = None


class SensorFunction():

    def __init__(self, uid=0, name="", args_datatypes=None, ret_datatype=None):
        self.log = logging.getLogger()
        self.uid = uid
        self.name = name
        self.__args_datatypes = []
        self.ret_datatype = None

        if isinstance(args_datatypes, list) and all(isinstance(arg, SensorDataType) for arg in args_datatypes):
            self.__args_datatypes = args_datatypes
        else:
            self.log.fatal('invalid argument type')

        if isinstance(ret_datatype, SensorDataType):
            self.__ret_datatype = ret_datatype
        else:
            self.log.fatal('invalid argument type')

    def append_arg_datatype(self, arg_datatype):
        if isinstance(arg_datatype, SensorDataType):
            self.__args_datatypes.append(arg_datatype)
        else:
            self.log.fatal('invalid argument type')

    def insert_arg_datatype(self, index, arg_datatype):
        if isinstance(arg_datatype, SensorDataType):
            self.__args_datatypes.insert(index, arg_datatype)
        else:
            self.log.fatal('invalid argument type')

    def set_args_datatypes(self, args_datatypes):
        if isinstance(args_datatypes, list) and all(isinstance(arg, SensorDataType) for arg in args_datatypes):
            self.__args_datatypes = args_datatypes
        else:
            self.log.fatal('invalid argument type')

    def get_args_datatypes(self):
        return self.__args_datatypes

    def get_arg_datatype(self, arg_index):
        return self.__args_datatypes.get(arg_index)

    def num_of_args(self):
        return len(self.__args_datatypes)

    def set_ret_datatype(self, ret_datatype):
        if isinstance(ret_datatype, SensorDataType):
            self.__ret_datatype = ret_datatype
        else:
            self.log.fatal('invalid argument type')


class SensorConnector():

    def __init__(self, uid=0, name=""):
        self.log = logging.getLogger('SensorConnector.' + name)
        self.uid = uid
        self.name = name
        self.__paramsIDs = {}
        self.__params = {}
        self.__funcsIDs = {}
        self.__funcs = {}
        self.__eventsIDs = {}
        self.__events = {}
        self.__measurementsIDs = {}
        self.__measurements = {}

    def add_parameter(self, param):
        if isinstance(param, SensorParameter):
            if param.uid not in self.__paramsIDs and param.name not in self.__params:
                self.__paramsIDs[param.uid] = param
                self.__params[param.name] = param
                return True
            else:
                self.log.info('already contains parameter %s with uid:%d', param.name, param.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_parameter(self, key):
        if isinstance(key, str):
            return self.__params.get(key)
        elif isinstance(key, int):
            return self.__paramsIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_parameters(self):
        return len(self.__params)

    def add_function(self, func):
        if isinstance(func, SensorFunction):
            if func.uid not in self.__funcsIDs and func.name not in self.__funcs:
                self.__funcsIDs[func.uid] = func
                self.__funcs[func.name] = func
                return True
            else:
                self.log.info('already contains function %s with uid:%d', func.name, func.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_function(self, key):
        if isinstance(key, str):
            return self.__funcs.get(key)
        elif isinstance(key, int):
            return self.__funcsIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_functions(self):
        return len(self.__funcs)

    def add_event(self, event):
        if isinstance(event, SensorEvent):
            if event.uid not in self.__eventsIDs and event.name not in self.__events:
                self.__eventsIDs[event.uid] = event
                self.__events[event.name] = event
                return True
            else:
                self.log.info('already contains event %s with uid:%d', event.name, event.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_event(self, key):
        if isinstance(key, str):
            return self.__events.get(key)
        elif isinstance(key, int):
            return self.__eventsIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_events(self):
        return len(self.__events)

    def add_measurement(self, measurement):
        if isinstance(measurement, SensorMeasurement):
            if measurement.uid not in self.__measurementsIDs and measurement.name not in self.__measurements:
                self.__measurementsIDs[measurement.uid] = measurement
                self.__measurements[measurement.name] = measurement
                return True
            else:
                self.log.info('already contains measurement %s with uid:%d', measurement.name, measurement.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_measurement(self, key):
        if isinstance(key, str):
            return self.__measurements.get(key)
        elif isinstance(key, int):
            return self.__measurementsIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_measurements(self):
        return len(self.__measurements)


class SensorNode():

    def __init__(self, serial_dev, node_id=0, interface=""):
        self.log = logging.getLogger('SensorNode.' + interface)
        self.serial_dev = serial_dev
        self.node_id = node_id
        self.interface = interface
        self.__datatypesIDs = {}
        self.__datatypes = {}
        self.__connectorsIDs = {}
        self.__connectors = {}

    def add_datatype(self, datatype):
        if isinstance(datatype, SensorDataType):
            if datatype.uid not in self.__datatypesIDs and datatype.name not in self.__datatypes:
                self.__datatypesIDs[datatype.uid] = datatype
                self.__datatypes[datatype.name] = datatype
                return True
            else:
                self.log.info('already contains datatype %s with uid:%d', datatype.name, datatype.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_datatype(self, key):
        if isinstance(key, str):
            return self.__datatypes.get(key)
        elif isinstance(key, int):
            return self.__datatypesIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_datatypes(self):
            return len(self.__datatypes)

    def add_connector(self, connector):
        if isinstance(connector, SensorConnector):
            if connector.uid not in self.__connectorsIDs and connector.name not in self.__connectors:
                self.__connectorsIDs[connector.uid] = connector
                self.__connectors[connector.name] = connector
                return True
            else:
                self.log.info('already contains connector %s with uid:%d', connector.name, connector.uid)
                return False
        else:
            self.log.fatal('invalid argument type')
            return False

    def get_connector(self, key):
        if isinstance(key, str):
            return self.__connectors.get(key)
        elif isinstance(key, int):
            return self.__connectorsIDs.get(key)
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_connectors(self):
            return len(self.__connectors)

    def add_parameter(self, connector, parameter):
        con = self.get_connector(connector)
        if con is not None:
            return con.add_parameter(parameter)

    def get_parameter(self, connector, parameter):
        con = self.get_connector(connector)
        if con is not None:
            return con.get_parameter(parameter)

    def num_of_parameters(self, connector=None):
        if connector is None:
            total = 0
            for con in self.__connectors:
                total += con.num_of_parameters()
            return total
        else:
            con = self.get_connector(connector)
            if con is not None:
                return con.num_of_parameters()

    def add_function(self, connector, function):
        con = self.get_connector(connector)
        if con is not None:
            return con.add_function(function)

    def get_function(self, connector, function):
        con = self.get_connector(connector)
        if con is not None:
            return con.get_function(function)

    def num_of_functions(self, connector=None):
        if connector is None:
            total = 0
            for con in self.__connectors:
                total += con.num_of_functions()
            return total
        else:
            con = self.get_connector(connector)
            if con is not None:
                return con.num_of_functions()

    def add_event(self, connector, event):
        con = self.get_connector(connector)
        if con is not None:
            return con.add_event(event)

    def get_event(self, connector, event):
        con = self.get_connector(connector)
        if con is not None:
            return con.get_event(event)

    def num_of_events(self, connector=None):
        if connector is None:
            total = 0
            for con in self.__connectors:
                total += con.num_of_events()
            return total
        else:
            con = self.get_connector(connector)
            if con is not None:
                return con.num_of_events()

    def add_measurement(self, connector, measurement):
        con = self.get_connector(connector)
        if con is not None:
            return con.add_measurement(measurement)

    def get_measurement(self, connector, measurement):
        con = self.get_connector(connector)
        if con is not None:
            return con.get_measurement(measurement)

    def num_of_measurements(self, connector=None):
        if connector is None:
            total = 0
            for con in self.__connectors:
                total += con.num_of_measurements()
            return total
        else:
            con = self.get_connector(connector)
            if con is not None:
                return con.num_of_measurements()

    @abc.abstractmethod
    def write_parameters(self, connector, param_key_values):
        pass

    @abc.abstractmethod
    def read_parameters(self, connector, param_keys):
        pass

    @abc.abstractmethod
    def read_measurements(self, connector, measurement_keys):
        pass

    @abc.abstractmethod
    def add_events_subscriber(self, connector, event_names, event_callback):
        pass

    @abc.abstractmethod
    def reset(self):
        pass

    def __str__(self):
        return "SensorNode. " + self.interface


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

                serial_dev = config.get(interface, 'SerialDev')

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
                    self.__nodes[interface] = CustomNode(serial_dev, mac_addr, ip_addr, interface, com_wrapper)
                elif node_type == 'ContikiRPCNode':
                    from .rpc_node import RPCNode
                    self.__nodes[interface] = RPCNode(serial_dev, node_id, interface, mac_addr, ip_addr, com_wrapper)
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
