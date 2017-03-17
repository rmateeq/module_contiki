import errno
import struct
import collections
from wishful_module_gitar.lib_gitar import ControlDataType, Parameter, Event
from wishful_module_gitar.lib_sensor import SensorNode


class RPCFuncHdr():

    fmt = struct.Struct("<BBBB")

    def __init__(self, con_uid, func_uid, num_of_args, args_len):
        self.con_uid = con_uid
        self.func_uid = func_uid
        self.num_of_args = num_of_args
        self.args_len = args_len

    def __len__(self):
        return RPCFuncHdr.fmt.size

    def __repr__(self):
        return "(C:%s,F:%s,NoA:%d,l:%d)" % (self.con_uid, self.func_uid, self.num_of_args, self.args_len)

    def to_bytes(self):
        return RPCFuncHdr.fmt.pack(self.con_uid, self.func_uid, self.num_of_args, self.args_len)


def read_RPCFuncHdr(message):
    con_uid, func_uid, num_of_args, args_len = RPCFuncHdr.fmt.unpack_from(message)
    return RPCFuncHdr(con_uid, func_uid, num_of_args, args_len)


def printRetCode(ret_code):
    if ret_code == 0:
        return "SUCCESS"
    elif ret_code in errno.errorcode:
        return errno.errorcode[ret_code]
    else:
        return "CODE NOT SUPPORTED"


class RPCRetHdr():

    fmt = struct.Struct("<BBB")

    def __init__(self, con_uid, func_uid, ret_code):
        self.con_uid = con_uid
        self.func_uid = func_uid
        self.ret_code = ret_code

    def __len__(self):
        return RPCRetHdr.fmt.size

    def __repr__(self):
        return "(C:%s,F:%s,RC:%s)" % (self.con_uid, self.func_uid, printRetCode(self.ret_code))

    def to_bytes(self):
        return RPCRetHdr.fmt.pack(self.con_uid, self.func_uid, self.ret_code)


def read_RPCRetHdr(message):
    con_uid, func_uid, ret_code = RPCRetHdr.fmt.unpack_from(message)
    return RPCRetHdr(con_uid, func_uid, ret_code)


# class RPCDataType(ControlDataType):

#     def __init__(self, uid=0, name="", size=0, endianness="<", fmt=""):
#         ControlDataType.__init__(self, uid, name, size, endianness, fmt)

#     def to_bytes(self, *args):
#         """
#         Transform value(s) to bytes specified by datatype format
#         ToDO work on variable size by using args[0]
#         """
#         try:
#             return struct.pack(self.endianness + self.fmt, *args)
#         except struct.error:
#             self.log.fatal('pack failed')

#     def read_bytes(self, buf):
#         """
#         Read value(s) from a buffer. Returns a tuple according to the datatype format
#         ToDO work on variable size by reading first byte
#         """
#         try:
#             return struct.unpack_from(self.endianness + self.fmt, buf)
#         except struct.error:
#             self.log.fatal('unpack failed')

#     def has_variable_size(self):
#         if self.size == 0:
#             return True
#         else:
#             return False


class RPCNode(SensorNode):

    def __init__(self, interface, platform, com_wrapper):
        SensorNode.__init__(self, interface, platform)
        self.com_wrapper = com_wrapper
        self.com_wrapper.add_event_callback(self.dispatch_event)

    def get_attr_by_key(self, attr_type, attr_key):
        attr = None
        for connector_name, connector_id in self.protocol_connectors.items():
            if attr_type == 'parameter':
                attr = self.get_parameter(connector_id, attr_key)
            elif attr_type == 'event':
                attr = self.get_event(connector_id, attr_key)
            elif attr_type == 'measurement':
                attr = self.get_measurement(connector_id, attr_key)
            if attr is not None:
                return attr
        if attr is None:
            self.log.info("Attr %s not found", attr_key)
        return None

    # def create_attribute_list_from_keys(self, attr_key_list, attr_type):
    #     attr_list = []
    #     for key in attr_key_list:
    #         attr = self.get_attr_by_key(attr_type, key)
    #         if attr is not None:
    #             attr_list.append(attr)
    #     return attr_list

    def create_bytearray_from_attr_list(self, attr_list, attr_args=None):
        b_array = bytearray()
        for attr in attr_list:
            b_array.extend(ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).to_bytes(attr.uid))
            if type(attr) == Parameter and attr_args is not None and type(attr_args) == dict:
                # b_array.extend(ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT8')).to_bytes(attr.datatype.size))
                b_array.extend(attr.datatype.to_bytes(attr_args[attr.name]))
            elif type(attr) == Event and attr_args is not None:
                b_array.extend(ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT32')).to_bytes(attr_args))
        return b_array

    def create_attr_key_value_from_bytearray(self, attr_type, num_attr, b_array):
        line_ptr = 0
        attr_key_value = {}
        for i in range(0, num_attr):
            attr_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(b_array[line_ptr:])
            line_ptr += 2
            attr = self.get_attr_by_key(attr_type, attr_uid)
            if attr is not None:
                attr_key_value[attr.name] = attr.datatype.read_bytes(b_array[line_ptr:])
                if attr.datatype.has_variable_size():
                    line_ptr += attr.datatype.calcsize(*attr_key_value[attr.name])
                else:
                    line_ptr += attr.datatype.size
        return attr_key_value

    def create_attr_key_error_from_bytearray(self, attr_type, num_attr, b_array):
        line_ptr = 0
        attr_key_error = {}
        for i in range(0, num_attr):
            attr_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(b_array[line_ptr:])
            line_ptr += 2
            attr = self.get_attr_by_key(attr_type, attr_uid)
            if attr is not None:
                attr_key_error[attr.name] = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('INT8')).read_bytes(b_array[line_ptr:])
                line_ptr += 1
        return attr_key_error

    def set_parameters2(self, parameter_list, param_key_values):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('set_parameters')
        b_array = self.create_bytearray_from_attr_list(parameter_list, param_key_values)
        request_message = bytearray()
        request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), len(b_array)).to_bytes())
        request_message.extend(b_array)
        response_message = self.com_wrapper.send(request_message)
        ret_hdr = read_RPCRetHdr(response_message)
        if ret_hdr.ret_code == 0:
            return self.create_attr_key_error_from_bytearray("parameter", len(parameter_list), response_message[len(ret_hdr):])
        return ret_hdr.ret_code

    def set_parameters(self, parameter_list, param_key_values):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('set_parameter')
        resp_key_values = {}
        for param in parameter_list:
            request_message = bytearray()
            dt_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16'))
            if param.datatype.has_variable_size():
                request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), dt_uid.size + param.datatype.calcsize(*param_key_values[param.name])).to_bytes())
            else:
                request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), dt_uid.size + param.datatype.size).to_bytes())
            request_message.extend(dt_uid.to_bytes(param.uid))
            # request_message.extend(ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT8')).to_bytes(param.datatype.size))
            if isinstance(param_key_values[param.name], collections.Sequence):
                request_message.extend(param.datatype.to_bytes(*param_key_values[param.name]))
            else:
                request_message.extend(param.datatype.to_bytes(param_key_values[param.name]))
            response_message = self.com_wrapper.send(request_message)
            line_ptr = 0
            ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
            line_ptr += len(ret_hdr)
            if ret_hdr.ret_code == 0:
                # p_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(response_message[line_ptr:])
                # line_ptr += 2
                resp_key_values[param.name] = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('INT8')).read_bytes(response_message[line_ptr:])
                line_ptr += 1
            else:
                resp_key_values[param.name] = ret_hdr.ret_code
        return resp_key_values

    def get_parameters2(self, parameter_list):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('get_parameters')
        b_array = self.create_bytearray_from_attr_list(parameter_list)
        request_message = bytearray()
        request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), len(b_array)).to_bytes())
        request_message.extend(b_array)
        response_message = self.com_wrapper.send(request_message)
        ret_hdr = read_RPCRetHdr(response_message)
        if ret_hdr.ret_code == 0:
            return self.create_attr_key_value_from_bytearray("parameter", len(parameter_list), response_message[len(ret_hdr):])
        return ret_hdr.ret_code

    def get_parameters(self, parameter_list):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('get_parameter')
        resp_key_values = {}
        for param in parameter_list:
            request_message = bytearray()
            dt_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16'))
            request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), dt_uid.size).to_bytes())
            request_message.extend(dt_uid.to_bytes(param.uid))
            response_message = self.com_wrapper.send(request_message)
            line_ptr = 0
            ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
            line_ptr += len(ret_hdr)
            if ret_hdr.ret_code == 0:
                # p_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(response_message[line_ptr:])
                # line_ptr += 2
                resp_key_values[param.name] = param.datatype.read_bytes(response_message[line_ptr:])
                if param.datatype.has_variable_size():
                    line_ptr += param.datatype.calcsize(*resp_key_values[param.name])
                else:
                    line_ptr += param.datatype.size
        return resp_key_values

    def read_measurements2(self, measurement_list):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('read_measurements')
        b_array = self.create_bytearray_from_attr_list(measurement_list)
        request_message = bytearray()
        request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), len(b_array)).to_bytes())
        request_message.extend(b_array)
        response_message = self.com_wrapper.send(request_message)
        ret_hdr = read_RPCRetHdr(response_message)
        if ret_hdr.ret_code == 0:
            return self.create_attr_key_value_from_bytearray("measurement", len(measurement_list), response_message[len(ret_hdr):])
        return ret_hdr.ret_code

    def read_measurements(self, measurement_list):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('read_measurement')
        resp_key_values = {}
        for measurement in measurement_list:
            request_message = bytearray()
            dt_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16'))
            request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), dt_uid.size).to_bytes())
            request_message.extend(dt_uid.to_bytes(measurement.uid))
            response_message = self.com_wrapper.send(request_message)
            line_ptr = 0
            ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
            line_ptr += len(ret_hdr)
            if ret_hdr.ret_code == 0:
                # p_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(response_message[line_ptr:])
                # line_ptr += 2
                resp_key_values[measurement.name] = measurement.datatype.read_bytes(response_message[line_ptr:])
                if measurement.datatype.has_variable_size():
                    line_ptr += measurement.datatype.calcsize(*resp_key_values[measurement.name])
                else:
                    line_ptr += measurement.datatype.size
        return resp_key_values

    def subscribe_events2(self, event_list, event_callback, event_duration):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('subscribe_events')
        b_array = self.create_bytearray_from_attr_list(event_list, event_duration)
        request_message = bytearray()
        request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), len(b_array)).to_bytes())
        request_message.extend(b_array)
        response_message = self.com_wrapper.send(request_message)
        ret_hdr = read_RPCRetHdr(response_message)
        if ret_hdr.ret_code == 0:
            event_key_error = self.create_attr_key_error_from_bytearray("parameter", len(event_list), response_message[len(ret_hdr):])
            for key in event_key_error:
                event_list[key].subscriber_callbacks.append(event_callback)
            return event_key_error
        return ret_hdr.ret_code

    def subscribe_events(self, event_list, event_callback, event_duration):
        generic_connector = self.get_connector("generic_connector")
        f = generic_connector.get_function('subscribe_event')
        resp_key_values = {}
        for event in event_list:
            request_message = bytearray()
            dt_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16'))
            dt_duration = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT32'))
            request_message.extend(RPCFuncHdr(generic_connector.uid, f.uid, f.num_of_args(), dt_uid.size + dt_duration.size).to_bytes())
            request_message.extend(dt_uid.to_bytes(event.uid))
            request_message.extend(dt_duration.to_bytes(event_duration))
            response_message = self.com_wrapper.send(request_message)
            line_ptr = 0
            ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
            line_ptr += len(ret_hdr)
            if ret_hdr.ret_code == 0:
                # p_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(response_message[line_ptr:])
                # line_ptr += 2
                resp_key_values[event.name] = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('INT8')).read_bytes(response_message[line_ptr:])
                line_ptr += 1
                event.subscriber_callbacks.append(event_callback)
                # line_ptr += event.datatype.size
        return resp_key_values

    def dispatch_event(self, event_msg):
        event_uid = ControlDataType(self.platform.endianness_fmt, self.platform.get_data_type_format_by_name('UINT16')).read_bytes(event_msg)
        event = self.get_attr_by_key("event", event_uid)
        event_value = event.datatype.read_bytes(event_msg[3:])
        print("RPC node {}: dispatching event {}: {} ".format(self.interface, event_uid, event_value))
        for subscriber_cb in event.subscriber_callbacks:
            subscriber_cb(event.name, event_value)

    def reset(self):
        pass

    def __str__(self):
        return "ContikiNode " + self.interface

    def forward_rpc(self, connector, fname, *fargs):
        c = self.get_connector(connector)
        # print("{} {} {} {}".format(connector, fname, fargs, len(fargs)))
        if c is not None:
            f = c.get_function(fname)
            if f is not None and len(f.get_args_datatypes()) == len(fargs):
                request_message = bytearray()
                args_len = 0
                # request_message.extend(RPCFuncHdr(c.uid, f.uid, f.num_of_args()).to_bytes())
                for i in range(0, len(fargs)):
                    # print("{} {} {}".format(f.get_args_datatypes()[i].size, f.get_args_datatypes()[i].fmt, fargs[i]))
                    request_message.extend(f.get_args_datatypes()[i].to_bytes(*fargs[i]))
                    args_len = args_len + f.get_args_datatypes()[i].size
                request_message = RPCFuncHdr(c.uid, f.uid, f.num_of_args(), args_len).to_bytes() + request_message
                response_message = self.com_wrapper.send(request_message)
                ret_hdr = read_RPCRetHdr(response_message)
                # print(ret_hdr)
                if ret_hdr.ret_code == 0:
                    if f.get_ret_datatype() is not None:
                        return f.get_ret_datatype().read_bytes(response_message[len(ret_hdr):])
            else:
                self.log.info("length argument list {} {} not correct {}".format(fargs, len(fargs), len(f.get_args_datatypes())))
                return None

    def execute_rpc(self, connector_uid, function_uid, function_def, num_args, args):
        request_message = bytearray()
        request_message.extend(RPCFuncHdr(connector_uid, function_uid, num_args).to_bytes())
        for i in range(0, len(args)):
            request_message.extend(function_def['args'][i].to_bytes(args[i]))
        response_message = self.com_wrapper.send(request_message)
        ret_hdr = read_RPCRetHdr(response_message)
        if ret_hdr.ret_code == 0:
            if function_def['ret'] is not None:
                return function_def['ret'].read_bytes(response_message[len(ret_hdr):])
