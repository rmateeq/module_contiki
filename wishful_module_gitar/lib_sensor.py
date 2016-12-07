import configparser as ConfigParser
import logging
import abc
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper
from communication_wrappers.coap_wrapper import CoAPWrapper
import struct
import sys
from wishful_module_gitar.lib_gitar import ProtocolConnector, ControlFunction, ControlAttribute


SIMPLE_DATATYPE_NAMES = [
    "BOOL",
    "CHAR",
    "UINT8",
    "INT8",
    "UINT16_LE",
    "INT16_LE",
    "UINT32_LE",
    "INT32_LE",
    "FLOAT32_LE",
    "UINT64_LE",
    "INT64_LE",
    "UINT16_BE",
    "INT16_BE",
    "UINT32_BE",
    "INT32_BE",
    "FLOAT32_BE",
    "UINT64_BE",
    "INT64_BE"
]

SIMPLE_DATATYPES_FORMATS = ["?", "c", "B", "b", "<H", "<h", "<I", "<i", "<f", "<Q", "<q", ">H", ">h", ">I", ">i", ">f", ">Q", ">q"]

SIMPLE_DATATYPE_NAMES_TO_FORMAT = {
    "BOOL": "?",
    "CHAR": "c",
    "UINT8": "B",
    "INT8": "b",
    "UINT16": "H",
    "INT16": "h",
    "UINT32": "I",
    "INT32": "i",
    "FLOAT32": "f",
    "UINT64": "Q",
    "INT64": "q"
}


class SensorDataType():

    to_string_byteorder = {'<': 'little', '>': 'big'}

    def __init__(self, endianness="", fmt=""):
        self.fmt = fmt
        if endianness != "":
            self.endianness = endianness
        elif sys.byteorder == 'little':
            self.endianness = '<'
        else:
            self.endianness = '>'

        # self.struct_fmt = struct.Struct(self.endianness + self.fmt)
        self.size = struct.calcsize(fmt)

    def to_bytes(self, *val):
        """
        Transform value(s) to bytes specified by datatype format
        """
        tmp_fmt = self.fmt
        if SensorDataType.to_string_byteorder[self.endianness] != sys.byteorder:
            tmp_fmt = self.endianness + self.fmt
        return struct.pack(tmp_fmt, *val)

    def read_bytes(self, buf):
        """
        Read value(s) from a buffer. Returns a tuple according to the datatype format
        """
        tmp_fmt = self.fmt
        if SensorDataType.to_string_byteorder[self.endianness] != sys.byteorder:
            tmp_fmt = self.endianness + self.fmt
        tpl = struct.unpack(tmp_fmt, buf)
        if len(tpl) == 1:
            tpl = tpl[0]
        return tpl

    def has_variable_size(self):
        if self.size == 0:
            return True
        return False


class SensorPlatform():

    DATATYPES = [
        "VOID",
        "BOOL",
        "CHAR",
        "UINT8",
        "INT8",
        "UINT16",
        "INT16",
        "UINT32",
        "INT32",
        "FLOAT32",
        "UINT64",
        "INT64",
        "USHORT",
        "SHORT",
        "UINT",
        "INT",
        "ULONG",
        "LONG",
        "STRING",
        "TLV",
        "OPAQUE"
    ]

    DATATYPE_NAMES_TO_FORMAT = {
        "BOOL": "?",
        "CHAR": "c",
        "UINT8": "B",
        "INT8": "b",
        "UINT16": "H",
        "INT16": "h",
        "UINT32": "I",
        "INT32": "i",
        "FLOAT32": "f",
        "UINT64": "Q",
        "INT64": "q",
        "OPAQUE": "",
        "VOID": "",
    }

    def __init__(self, endianness_fmt):
        self.__dt_formats_by_id = {}
        self.__dt_formats_by_name = {}
        self.endianness_fmt = endianness_fmt
        for dt_name, dt_format in SensorPlatform.DATATYPE_NAMES_TO_FORMAT.items():
            self.__dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.__dt_formats_by_name[dt_name] = dt_format

    def get_data_type_format_by_id(self, id):
        if id in self.__dt_formats_by_id:
            return self.__dt_formats_by_id[id]
        return None

    def get_data_type_format_by_name(self, name):
        if name in self.__dt_formats_by_name:
            return self.__dt_formats_by_name[name]
        return None

    def get_supported_datatypes(self):
        return SensorPlatform.DATATYPES

    @classmethod
    def create_instance(cls, module_name, class_name):
        py_module = __import__(module_name)
        globals()[module_name] = py_module
        module_class = getattr(py_module, class_name)
        module = module_class()
        print(module)
        return module


class SensorNode():
    __metaclass__ = abc.ABCMeta

    def __init__(self, serial_dev, node_id=0, interface="", platform):
        self.log = logging.getLogger('SensorNode.' + interface)
        self.serial_dev = serial_dev
        self.node_id = node_id
        self.interface = interface
        self.platform = platform
        self.__connectorsIDs = {}
        self.__connectors = {}

    def add_connector(self, connector):
        if isinstance(connector, ProtocolConnector):
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

    def get_connector_ids(self):
        return self.__connectorsIDs.keys()

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
                    com_wrapper = SerialdumpWrapper(serial_dev, interface)
                elif com_method == 'CoAP':
                    com_wrapper = CoAPWrapper(ip_addr, node_id, serial_dev)
                else:
                    self.log.fatal('invalid CommunicationMethod')

                platform_class = config.get(interface, 'PlatformClass')
                platform_module = config.get(interface, 'PlatformModule')
                platform = SensorPlatform.create_instance(platform_class, platform_module)

                # Create a specific type of node
                node_type = config.get(interface, 'NodeType')
                if node_type == 'ContikiCustomNode':
                    from .custom_node import CustomNode
                    self.__nodes[interface] = CustomNode(serial_dev, mac_addr, ip_addr, interface, com_wrapper, platform)
                elif node_type == 'ContikiRPCNode':
                    from .rpc_node import RPCNode
                    self.__nodes[interface] = RPCNode(serial_dev, node_id, interface, mac_addr, ip_addr, com_wrapper, platform)
                else:
                    self.log.fatal('invalid NodeType')

            else:
                self.log.info('Skipping interface %s', interface)

    def __create_control_attribute(self, uid, uname, category):
        if category == "PARAMETER":
            return Parameter(uid, uname)
        elif category == "MEASUREMENT":
            return Measurement(uid, uname)
        elif category == "EVENT":
            return Event(uid, uname)
        else:
            return None

    def __add_control_attribute(self, ctrl_attr, category):
        if category == "PARAMETER":
            self.add_parameter(ctrl_attr)
        elif category == "MEASUREMENT":
            self.add_measurement(ctrl_attr)
        elif category == "EVENT":
            self.add_event(ctrl_attr)
        pass

    def parse_control_attributes(self, csv_filename, node):
        if csv_filename != '':
            try:
                file_rp = open(csv_filename, 'rt')
                attributes = csv.DictReader(file_rp)
                for attribute_def in attributes:
                    ctrl_attr = self.__create_control_attribute(int(attribute_def["unique_id"]), attribute_def["unique_name"], attribute_def["category"])
                    if attribute_def["format"] in SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT:
                        ctrl_attr.set_datatype(SensorDataType(attribute_def["endianness"], SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT[attribute_def["format"]]))
                    else:
                        ctrl_attr.set_datatype(SensorDataType(attribute_def["endianness"], attribute_def["format"]))
                    if ctrl_attr is not None:
                        self.__add_control_attribute(ctrl_attr, attribute_def["category"])
            except Exception as e:
                self.log.fatal("Could not read parameters for %s, from %s error: %s" % (self.name, csv_filename, e))

    def parse_control_functions(self, csv_filename, node):
        if csv_filename != '':
            try:
                file_rp = open(csv_filename, 'rt')
                functions = csv.DictReader(file_rp)
                for function_def in functions:
                    ctrl_fnct = ControlFunction(int(function_def["unique_id"]), function_def["unique_name"])
                    fnct_fmt = function_def["format"]
                    if fnct_fmt != "":
                        ret_type = fnct_fmt.split(":")[0]
                        if ret_type in SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT:
                            ctrl_fnct.set_ret_datatype(SensorDataType(function_def["endianness"], SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT[ret_type]))
                        else:
                            ctrl_fnct.set_ret_datatype(SensorDataType(function_def["endianness"], fnct_fmt))
                        for arg_type in fnct_fmt.split(":")[1].split(";"):
                            if arg_type in SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT:
                                ctrl_fnct.append_arg_datatype(SensorDataType(function_def["endianness"], SensorNode.SIMPLE_DATATYPE_NAMES_TO_FORMAT[arg_type]))
                            else:
                                ctrl_fnct.append_arg_datatype(SensorDataType(function_def["endianness"], fnct_fmt))
                    self.add_function(ctrl_fnct)
            except Exception as e:
                self.log.fatal("Could not read parameters for %s, from %s error: %s" % (self.name, csv_filename, e))

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


def parse_attribute_format_specifier(fmt_specifier, platform):
    if ";" not in fmt_specifier:
        # simple format (non-struct type or directly in struct format)
        if fmt_specifier not in SensorPlatform.DATATYPES:
            # assume struct format
            return fmt_specifier
        else:
            return platform.get_data_type_format_by_name(fmt_specifier)
    else:
        dt_strct_fmt = ""
        # cannot be a struct format (e.g. HHB), but a format specifier for structs (UINT16;UINT16;UINT8) so parse it as such
        if '(' not in fmt_specifier:
            # the format does not contain substructs
            for subformat in fmt_specifier.split(";"):
                dt_strct_fmt = dt_strct_fmt + platform.get_data_type_format_by_name(subformat)
            return dt_strct_fmt
        else:
            find_substruct(fmt_specifier, platform)


def find_substruct(fmt_specifier, platform):
    ind = fmt_specifier.find('(')
    struct_fmt = ""
    if '(' in fmt_specifier[ind:len(fmt_specifier)]:
        struct_fmt = struct_fmt + find_substruct(fmt_specifier[ind:len(fmt_specifier)], platform)
    ind2 = fmt_specifier.find(')')
    for el in fmt_specifier[ind, ind2].split(";"):
        struct_fmt = struct_fmt + platform.get_data_type_format_by_name(el)

def split_format_specifier(fmt_specifier, parent_index):
    closing_brackets = {'{': '}', '[': ']'}
    if fmt_specifier != "":
        sub_index = "1"
        sub_hash = {}
        begin_pos = 0
        split_pos = 0
        while(split_pos != -1):
            split_pos = fmt_specifier.find(";")
            prefix = fmt_specifier[begin_pos:split_pos]
            suffix = fmt_specifier[split_pos:]
            if prefix[0] == '{' or prefix[0] == '[':
                pos = find_matching_bracket(suffix, prefix[0], closing_brackets[prefix[0]])

            else:
                sub_hash[parent_index + sub_index] = sub_str
                begin_pos = split_pos + 1
                sub_index = str(int(sub_index) + 1)
        return sub_hash


from construct import *

construct_map = {"u1": Int8ul, "u2": Int16ul, "u4": Int32ul}

def bla(fmt_map, key):
    return 

def create_construct(fmt_map):
    lst_ret = []
    print("calling construct on {}".format(fmt_map))
    for key in sorted(fmt_map.keys()):
        print(key)
        if type(fmt_map[key]) == dict:
            c = create_construct(fmt_map[key])
            if fmt_map[key]['type'] == "array":
                array_len = fmt_map[key]['len']
                print("Creating Array {} len {}".format(c, array_len))
                if int(array_len) > 0:
                    lst_ret.append(key / Array(int(array_len), Struct(*c)))
                else:
                    # relative to previous element
                    ind_key = str(int(key) + int(array_len))
                    print(ind_key)
                    lst_ret.append(key / Array(lambda ctx: ctx[ind_key], Struct(*c)))
                    print("bla")
            elif fmt_map[key]['type'] == "struct":
                print("Creating struct {}".format(c))
                lst_ret.append(key / Struct(*c))
        elif key != 'type' and key != 'len':
            lst_ret.append(key / construct_map[fmt_map[key]])
    print(lst_ret)
    return tuple(lst_ret)


def nog_eki(fmt_specifier, fmt_map, parent_index):
    brackets_open = "{["
    brackets_close = "}]"
    sub_index = "1"
    begin_pos = 0
    end_pos = -1
    while begin_pos < len(fmt_specifier):
        print(begin_pos)
        print(fmt_specifier[begin_pos:])
        if fmt_specifier[begin_pos] == "":
            return
        elif fmt_specifier[begin_pos] in brackets_open:
            ind = brackets_open.index(fmt_specifier[begin_pos])
            begin_pos = begin_pos + 1
            end_pos = begin_pos + find_matching_bracket(fmt_specifier[begin_pos:], brackets_open[ind], brackets_close[ind])
            print("{} {}".format(begin_pos, end_pos))
            fmt_map[parent_index + sub_index] = {}
            if brackets_open[ind] == "[":
                fmt_map[parent_index + sub_index]["type"] = "array"
                tmp_pos = fmt_specifier[begin_pos:end_pos].find(";")
                fmt_map[parent_index + sub_index]["len"] = fmt_specifier[begin_pos:begin_pos + tmp_pos]
                begin_pos = begin_pos + tmp_pos + 1
            elif brackets_open[ind] == "{":
                fmt_map[parent_index + sub_index]["type"] = "struct"
            print("substruct: " + parent_index + "." + sub_index + " " + fmt_specifier[begin_pos:end_pos])
            nog_eki(fmt_specifier[begin_pos:end_pos], fmt_map[parent_index + sub_index], parent_index + sub_index)
            print(sub_index)
            sub_index = str(int(sub_index) + 1)
        else:
            end_pos = begin_pos + fmt_specifier[begin_pos:].find(";")
            print("{} {}".format(begin_pos, end_pos))
            if end_pos == begin_pos - 1:
                print(parent_index + "." + sub_index + ": " + fmt_specifier[begin_pos:])
                fmt_map[parent_index + sub_index] = fmt_specifier[begin_pos:]
                return
            elif fmt_specifier[begin_pos] != ';':
                print(parent_index + "." + sub_index + ": " + fmt_specifier[begin_pos:end_pos])
                fmt_map[parent_index + sub_index] = fmt_specifier[begin_pos:end_pos]
                sub_index = str(int(sub_index) + 1)
        begin_pos = end_pos + 1


def find_matching_bracket(fmt_specifier, bracket_open, bracket_close):
    print("{} {} {}".format(fmt_specifier, bracket_open, bracket_close))
    bracket_open_stack = []
    for i, c in enumerate(fmt_specifier):
        if c == bracket_open:
            bracket_open_stack.append(i)
        elif c == bracket_close:
            if not bracket_open_stack:
                return i
            bracket_open_stack.pop()
    return -1


def pair_brackets(fmt_specifier):
    brackets_open = "{["
    brackets_close = "}]"
    bracket_ranges = {brackets_open.index('{'): [], brackets_open.index('['): []}
    bracket_open_stack = {brackets_open.index('{'): [], brackets_open.index('['): []}
    for i, c in enumerate(fmt_specifier):
        if c in brackets_open:
            bracket_open_stack[brackets_open.index(c)].append(i)
        elif c in brackets_close:
            pos = bracket_open_stack[brackets_close.index(c)].pop()
            bracket_ranges[brackets_close.index(c)].append([pos, i])
    print(fmt_specifier)
    print(bracket_ranges)
    print(bracket_open_stack)
