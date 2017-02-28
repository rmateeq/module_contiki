import logging
import sys
import struct


class ControlDataType():

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
        if ControlDataType.to_string_byteorder[self.endianness] != sys.byteorder:
            tmp_fmt = self.endianness + self.fmt
        return struct.pack(tmp_fmt, *val)

    def read_bytes(self, buf):
        """
        Read value(s) from a buffer. Returns a tuple according to the datatype format
        """
        tmp_fmt = self.fmt
        if ControlDataType.to_string_byteorder[self.endianness] != sys.byteorder:
            tmp_fmt = self.endianness + self.fmt
        tpl = struct.unpack(tmp_fmt, buf)
        if len(tpl) == 1:
            tpl = tpl[0]
        return tpl

    def has_variable_size(self):
        if self.size == 0:
            return True
        return False


class ControlAttribute():

    def __init__(self, uid=0, name="", datatype=None):
        self.log = logging.getLogger()
        self.uid = uid
        self.name = name
        self.datatype = None

        if datatype is not None and isinstance(datatype, ControlDataType):
            self.datatype = datatype

    def set_datatype(self, datatype):
        if isinstance(datatype, ControlDataType):
            self.datatype = datatype
        else:
            self.log.fatal('invalid argument type bla')


class Parameter(ControlAttribute):

    def __init__(self, uid=0, name="", datatype=None):
        ControlAttribute.__init__(self, uid, name, datatype)
        self.change_list = []


class Event(ControlAttribute):

    def __init__(self, uid=0, name="", datatype=None):
        ControlAttribute.__init__(self, uid, name, datatype)
        self.event_duration = 0
        self.subscriber_callbacks = []


class Measurement(ControlAttribute):

    def __init__(self, uid=0, name="", datatype=None):
        ControlAttribute.__init__(self, uid, name, datatype)
        self.is_periodic = False
        self.read_interval = 0
        self.report_interval = 0
        self.num_iterations = 0
        self.report_callback = None


class ControlFunction():

    def __init__(self, uid=0, name="", args_datatypes=None, ret_datatype=None):
        self.log = logging.getLogger()
        self.uid = uid
        self.name = name
        self.__args_datatypes = []
        self.__ret_datatype = None

        if args_datatypes is not None and isinstance(args_datatypes, list) and all(isinstance(arg, ControlDataType) for arg in args_datatypes):
            self.__args_datatypes = args_datatypes

        if ret_datatype is not None and isinstance(ret_datatype, ControlDataType):
            self.__ret_datatype = ret_datatype

    def append_arg_datatype(self, arg_datatype):
        if isinstance(arg_datatype, ControlDataType):
            self.__args_datatypes.append(arg_datatype)
        else:
            self.log.fatal('invalid argument type 2')

    def insert_arg_datatype(self, index, arg_datatype):
        if isinstance(arg_datatype, ControlDataType):
            self.__args_datatypes.insert(index, arg_datatype)
        else:
            self.log.fatal('invalid argument type 3')

    def set_args_datatypes(self, args_datatypes):
        if isinstance(args_datatypes, list) and all(isinstance(arg, ControlDataType) for arg in args_datatypes):
            self.__args_datatypes = args_datatypes
        else:
            self.log.fatal('invalid argument type 4')

    def get_args_datatypes(self):
        return self.__args_datatypes

    def get_arg_datatype(self, arg_index):
        return self.__args_datatypes.get(arg_index)

    def num_of_args(self):
        return len(self.__args_datatypes)

    def set_ret_datatype(self, ret_datatype):
        if isinstance(ret_datatype, ControlDataType):
            self.__ret_datatype = ret_datatype
        else:
            self.log.fatal('invalid argument type 5')

    def get_ret_datatype(self):
        return self.__ret_datatype


class ProtocolConnector():

    def __init__(self, uid=0, name=""):
        self.log = logging.getLogger('ProtocolConnector.' + name)
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
        if isinstance(param, Parameter):
            if param.uid not in self.__paramsIDs and param.name not in self.__params:
                self.__paramsIDs[param.uid] = param
                self.__params[param.name] = param
                return True
            else:
                self.log.info('already contains parameter %s with uid:%d', param.name, param.uid)
                return False
        else:
            self.log.fatal('invalid argument type 6')
            return False

    def get_parameter(self, key):
        if isinstance(key, str):
            if key in self.__params:
                return self.__params[key]
            else:
                return None
        elif isinstance(key, int):
            if key in self.__paramsIDs:
                return self.__paramsIDs[key]
            else:
                return None
        else:
            self.log.fatal('invalid argument type 7')
            return None

    def num_of_parameters(self):
        return len(self.__params)

    def add_function(self, func):
        if isinstance(func, ControlFunction):
            if func.uid not in self.__funcsIDs and func.name not in self.__funcs:
                self.__funcsIDs[func.uid] = func
                self.__funcs[func.name] = func
                return True
            else:
                self.log.info('already contains function %s with uid:%d', func.name, func.uid)
                return False
        else:
            self.log.fatal('invalid argument type 8')
            return False

    def get_function(self, key):
        # print(key)
        if isinstance(key, str):
            return self.__funcs.get(key)
        elif isinstance(key, int):
            return self.__funcsIDs.get(key)
        else:
            self.log.fatal('invalid argument type 9')
            return None

    def num_of_functions(self):
        return len(self.__funcs)

    def add_event(self, event):
        if isinstance(event, Event):
            if event.uid not in self.__eventsIDs and event.name not in self.__events:
                self.__eventsIDs[event.uid] = event
                self.__events[event.name] = event
                return True
            else:
                self.log.info('already contains event %s with uid:%d', event.name, event.uid)
                return False
        else:
            self.log.fatal('invalid argument type 10')
            return False

    def get_event(self, key):
        if isinstance(key, str):
            if key in self.__events:
                return self.__events[key]
            else:
                return None
        elif isinstance(key, int):
            if key in self.__eventsIDs:
                return self.__eventsIDs[key]
            else:
                return None
        else:
            self.log.fatal('invalid argument type')
            return None

    def num_of_events(self):
        return len(self.__events)

    def add_measurement(self, measurement):
        if isinstance(measurement, Measurement):
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
            if key in self.__measurements:
                return self.__measurements[key]
            else:
                return None
        elif isinstance(key, int):
            if key in self.__measurementsIDs:
                return self.__measurementsIDs[key]
            else:
                return None
        else:
            self.log.fatal('invalid argument type')

    def num_of_measurements(self):
        return len(self.__measurements)
