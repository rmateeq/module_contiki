import configparser as ConfigParser
import logging
import abc
from communication_wrappers.serialdump_wrapper import SerialdumpWrapper
from communication_wrappers.coap_wrapper import CoAPWrapper
import csv
from wishful_module_gitar.lib_gitar import ProtocolConnector, ControlFunction, ControlDataType, OpaqueControlDataType, Parameter, Event, Measurement
import traceback
import sys
import subprocess
import gevent
# from .rpc_node import RPCNode

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
        "ULONGLONG",
        "LONGLONG",
        "FLOAT",
        "DOUBLE",
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
        self.dt_formats_by_id = {}
        self.dt_formats_by_name = {}
        self.endianness_fmt = endianness_fmt
        for dt_name, dt_format in SensorPlatform.DATATYPE_NAMES_TO_FORMAT.items():
            self.dt_formats_by_id[SensorPlatform.DATATYPES.index(dt_name)] = dt_format
            self.dt_formats_by_name[dt_name] = dt_format

    def get_data_type_format_by_id(self, id):
        if id in self.dt_formats_by_id:
            return self.dt_formats_by_id[id]
        return None

    def get_data_type_format_by_name(self, name):
        if name in self.dt_formats_by_name:
            return self.dt_formats_by_name[name]
        return None

    def get_supported_datatypes(self):
        return SensorPlatform.DATATYPES

    @classmethod
    def create_instance(cls, module_name, class_name):
        import importlib
        py_module = importlib.import_module("wishful_module_gitar." + module_name)
        # py_module = __import__("wishful_module_gitar." + module_name)
        globals()[module_name] = py_module
        module_class = getattr(py_module, class_name)
        module = module_class()
        print(module)
        return module


class SensorNode():
    __metaclass__ = abc.ABCMeta

    def __init__(self, interface, platform):
        self.log = logging.getLogger('SensorNode.' + interface)
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
        if isinstance(key, ProtocolConnector):
            return key
        elif isinstance(key, str):
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
    def set_parameters(self, param_list, param_key_values):
        pass

    @abc.abstractmethod
    def get_parameters(self, param_list):
        pass

    @abc.abstractmethod
    def read_measurements(self, measurement_list, measurement_keys):
        pass

    @abc.abstractmethod
    def add_events_subscriber(self, event_list, event_callback, event_duration):
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

    def create_nodes_auto(self):
        from .rpc_node import RPCNode
        # motelist_output = subprocess.check_output(["../../agent_modules/contiki/communication_wrappers/bin/motelist", "-c"], universal_newlines=True)
        # for line in motelist_output.strip().split("\n"):
        #     mote_description = line.split(",")[2]
        #     mote_dev = line.split(",")[1]
        #     mote_dev_id = ""
        #     for char in mote_dev:
        #         if char.isdigit():
        #             mote_dev_id = mote_dev_id + char
        #     interface = "lowpan" + mote_dev_id
        #     mote_dev_id = int(mote_dev_id) + 1
        #     if "Zolertia RE-Mote" in mote_description:
        #         # device is a remote
        #         platform_class = "Zoul"
        #         platform_module = "lib_arm_cortex_m"
        #         self.log.info("cc2538-bsl.py  -p %s -a 0x00202000", mote_dev)
        #         # compl_proc = subprocess.run(["../../agent_modules/contiki/communication_wrappers/bin/cc2538-bsl.py", "-p", mote_dev, "-a", "0x00202000"], stdout=subprocess.PIPE)
        #         # self.log.info(compl_proc.stdout)
        #         out = subprocess.check_output(["../../agent_modules/contiki/communication_wrappers/bin/cc2538-bsl.py", "-p", mote_dev, "-a", "0x00202000"])
        #         self.log.info(out)
        #         self.log.info("Found Zoul on %s", mote_dev)
        #         com_wrapper = CoAPWrapper(mote_dev_id, mote_dev, "115200")
        #     elif "RM090" in mote_description:
        #         # defince is a RM090
        #         platform_class = "RM090"
        #         platform_module = "lib_msp430"
        #         self.log.info("Found RM090 on %s", mote_dev)
        #         com_wrapper = CoAPWrapper(mote_dev_id, mote_dev, "230400")
        #     else:
        #         self.log.info("skipping unknown node type")
        #         break
        #     platform = SensorPlatform.create_instance(platform_module, platform_class)
        #     self.__nodes[interface] = RPCNode(interface, platform, com_wrapper)
        motelist_output = subprocess.check_output(["../../agent_modules/contiki/communication_wrappers/bin/motelist", "-c"], universal_newlines=True).strip()
        if motelist_output == "No devices found.":
            # check if there are cooja devices!
            try:
                cooja_devs = subprocess.check_output("ls -1v /dev/cooja_rm090* 2>/dev/null", shell=True, universal_newlines=True).strip().split("\n")
                for i, cooja_dev in enumerate(cooja_devs):
                    platform_class = "RM090"
                    platform_module = "lib_msp430"
                    com_wrapper = CoAPWrapper(i + 1, cooja_dev, "115200", "500")  # Jan: 500 serial delay for taisc (writing to serial while in interrupt causes issues)
                    platform = SensorPlatform.create_instance(platform_module, platform_class)
                    interface = "lowpan" + str(i)
                    self.__nodes[interface] = RPCNode(interface, platform, com_wrapper)
            except subprocess.CalledProcessError:
                self.log.fatal("There are no sensor nodes attached to this machine, and there are no cooja devices, cannot start!!!")
        else:
            for line in motelist_output.split("\n"):
                mote_description = line.split(",")[2]
                mote_dev = line.split(",")[1]
                mote_dev_id = ""
                for char in mote_dev:
                    if char.isdigit():
                        mote_dev_id = mote_dev_id + char
                interface = "lowpan" + mote_dev_id
                mote_dev_id = int(mote_dev_id) + 1
                if "Zolertia RE-Mote" in mote_description:
                    # device is a remote
                    platform_class = "Zoul"
                    platform_module = "lib_arm_cortex_m"
                    self.log.info("cc2538-bsl.py  -p %s -a 0x00202000", mote_dev)
                    # compl_proc = subprocess.run(["../../agent_modules/contiki/communication_wrappers/bin/cc2538-bsl.py", "-p", mote_dev, "-a", "0x00202000"], stdout=subprocess.PIPE)
                    # self.log.info(compl_proc.stdout)
                    out = subprocess.check_output(["sudo ../../agent_modules/contiki/communication_wrappers/bin/cc2538-bsl.py", "-p", mote_dev, "-a", "0x00202000"])
                    self.log.info(out)
                    self.log.info("Found Zoul on %s", mote_dev)
                    gevent.sleep(2)
                    com_wrapper = CoAPWrapper(mote_dev_id, mote_dev, "115200")
                elif "RM090" in mote_description:
                    # defince is a RM090
                    platform_class = "RM090"
                    platform_module = "lib_msp430"
                    self.log.info("Found RM090 on %s", mote_dev)
                    com_wrapper = CoAPWrapper(mote_dev_id, mote_dev, "115200", "500")
                else:
                    self.log.info("skipping unknown node type")
                    break
                platform = SensorPlatform.create_instance(platform_module, platform_class)
                self.__nodes[interface] = RPCNode(interface, platform, com_wrapper)

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
                platform = SensorPlatform.create_instance(platform_module, platform_class)

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

    def __add_control_attribute(self, node, ctrl_attr, category, connector):
        if category == "PARAMETER":
            node.add_parameter(connector, ctrl_attr)
        elif category == "MEASUREMENT":
            node.add_measurement(connector, ctrl_attr)
        elif category == "EVENT":
            node.add_event(connector, ctrl_attr)
        pass

    def __parse_struct_attribute(self, node_platform, fmt_specifier):
        struct_fmt = ""
        for strct_el_specifier in fmt_specifier.split(";"):
            struct_fmt = struct_fmt + node_platform.get_data_type_format_by_name(strct_el_specifier)
        return struct_fmt

    def parse_control_attributes(self, csv_filename, node, connector):
        if csv_filename != '':
            try:
                file_rp = open(csv_filename, 'rt')
                attributes = csv.DictReader(file_rp)
                for attribute_def in attributes:
                    ctrl_attr = self.__create_control_attribute(int(attribute_def["unique_id"]), attribute_def["unique_name"], attribute_def["category"])
                    if attribute_def["sub_format"] == "":
                        if attribute_def["format"] in node.platform.get_supported_datatypes():
                            ctrl_attr.set_datatype(ControlDataType(attribute_def["endianness"], node.platform.get_data_type_format_by_name(attribute_def["format"])))
                        else:
                            # ctrl_attr.set_datatype(ControlDataType(attribute_def["endianness"], attribute_def["format"]))
                            ctrl_attr.set_datatype(ControlDataType(attribute_def["endianness"], self.__parse_struct_attribute(node.platform, attribute_def["format"])))
                    else:
                        fmt = ""
                        sub_fmt = ""
                        if attribute_def["format"] in node.platform.get_supported_datatypes():
                            fmt = node.platform.get_data_type_format_by_name(attribute_def["format"])
                        else:
                            fmt = self.__parse_struct_attribute(node.platform, attribute_def["format"])
                        if attribute_def["sub_format"] in node.platform.get_supported_datatypes():
                            sub_fmt = node.platform.get_data_type_format_by_name(attribute_def["sub_format"])
                        else:
                            sub_fmt = self.__parse_struct_attribute(node.platform, attribute_def["sub_format"])
                        ctrl_attr.set_datatype(OpaqueControlDataType(attribute_def["endianness"], fmt, sub_fmt))
                    if ctrl_attr is not None:
                        self.__add_control_attribute(node, ctrl_attr, attribute_def["category"], connector)
                    # print("\"{}\",".format(attribute_def["unique_name"]))
            except Exception as e:
                self.log.fatal("Could not read parameters %s from %s error: %s" % (attribute_def, csv_filename, e))

    def __parse_struct_param(self, node_platform, fmt_specifier):
        struct_fmt = ""
        for strct_el_specifier in fmt_specifier.split("|"):
            # print(strct_el_specifier)
            struct_fmt = struct_fmt + node_platform.get_data_type_format_by_name(strct_el_specifier)
        return struct_fmt

    def parse_control_functions(self, csv_filename, node, connector):
        if csv_filename != '':
            try:
                file_rp = open(csv_filename, 'rt')
                functions = csv.DictReader(file_rp)
                for function_def in functions:
                    # print("{}{}".format(function_def["unique_id"], function_def["unique_name"]))
                    ctrl_fnct = ControlFunction(int(function_def["unique_id"]), function_def["unique_name"])
                    fnct_fmt = function_def["format"]
                    if fnct_fmt != "":
                        ret_type = fnct_fmt.split(":")[0]
                        if ret_type in node.platform.get_supported_datatypes():
                            ctrl_fnct.set_ret_datatype(ControlDataType(function_def["endianness"], node.platform.get_data_type_format_by_name(ret_type)))
                        else:
                            # ctrl_fnct.set_ret_datatype(ControlDataType(function_def["endianness"], fnct_fmt))
                            ctrl_fnct.set_ret_datatype(ControlDataType(function_def["endianness"], self.__parse_struct_param(node.platform, ret_type)))
                        for arg_type in fnct_fmt.split(":")[1].split(";"):
                            if arg_type != "":
                                if arg_type in node.platform.get_supported_datatypes():
                                    ctrl_fnct.append_arg_datatype(ControlDataType(function_def["endianness"], node.platform.get_data_type_format_by_name(arg_type)))
                                else:
                                    # ctrl_fnct.append_arg_datatype(ControlDataType(function_def["endianness"], fnct_fmt))
                                    ctrl_fnct.append_arg_datatype(ControlDataType(function_def["endianness"], self.__parse_struct_param(node.platform, arg_type)))
                    node.add_function(connector, ctrl_fnct)
            except Exception as e:
                traceback.print_exc(file=sys.stdout)
                self.log.fatal("Could not read parameters from %s error: %s" % (csv_filename, e))

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

le_platform_cnstrct_map = ["uS", "sS", "uI", "sI", "uL", "sL", "uF", "sF", "uD", "sD"]
le_base_cnstrct_map = {"u1": Int8ul, "u2": Int16ul, "u4": Int32ul, "u8": Int64ul, "i1": Int8sl, "i2": Int16sl, "i4": Int32sl, "i8": Int64sl, "f4": Float32l, "f8": Float64l}
be_construct_map = {}

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


def parse_format_specifier(fmt_specifier, fmt_map, parent_index):
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
            parse_format_specifier(fmt_specifier[begin_pos:end_pos], fmt_map[parent_index + sub_index], parent_index + sub_index)
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
