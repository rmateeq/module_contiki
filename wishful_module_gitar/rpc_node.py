import errno
import struct

from wishful_module_gitar.lib_gitar import *


class RPCFuncHdr():

    fmt = struct.Struct("<BBB")

    def __init__(self, con_uid, func_uid, num_of_args):
        self.con_uid = con_uid
        self.func_uid = func_uid
        self.num_of_args = num_of_args

    def __len__(self):
        return RPCFuncHdr.fmt.size

    def __repr__(self):
        return "(C:%s,F:%s,NoA:%d)" % (self.con_uid, self.func_uid, self.num_of_args)

    def to_bytes(self):
        return RPCFuncHdr.fmt_func_header.pack(self.con_uid, self.func_uid, self.num_of_args)


def read_RPCFuncHdr(message):
    con_uid, func_uid, num_of_args = RPCFuncHdr.fmt.unpack_from(message)
    return RPCFuncHdr(con_uid, func_uid, num_of_args)


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


class RPCDataType(SensorDataType):

    def __init__(self, uid=0, name="", size=0, endianness="<", fmt=""):
        SensorDataType.__init__(self, uid, name, size, endianness, fmt)

    def to_bytes(self, *args):
        """
        Transform value(s) to bytes specified by datatype format
        ToDO work on variable size by using args[0]
        """
        try:
            return struct.pack(self.endianness + self.fmt, *args)
        except struct.error:
            self.log.fatal('pack failed')

    def read_bytes(self, buf):
        """
        Read value(s) from a buffer. Returns a tuple according to the datatype format
        ToDO work on variable size by reading first byte
        """
        try:
            return struct.unpack_from(self.endianness + self.fmt, buf)
        except struct.error:
            self.log.fatal('unpack failed')

    def has_variable_size(self):
        if self.size == 0:
            return True
        else:
            return False


class RPCNode(SensorNode):

    def __init__(self, serial_dev, node_id=0, interface="", mac_addr="", ip_addr="", com_wrapper=None):
        SensorNode.__init__(self, serial_dev, node_id, interface)
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.com_wrapper = com_wrapper

    def write_parameters(self, connector, param_key_values):
        c = self.get_connector(connector)
        if c is not None:
            f = c.get_function('SETPARAMETER')
            if f is not None:
                request_message = bytearray()
                req_keys = []
                for key, value in param_key_values:
                    p = c.get_parameter(key)
                    if p is not None:
                        request_message.extend(RPCFuncHdr(c.uid, f.uid, f.num_of_args()).to_bytes())
                        request_message.extend(self.get_datatype('UINT16').to_bytes(p.uid))
                        if p.datatype.has_variable_size():
                            # ToDO work on variable size by writing first byte
                            pass
                        request_message.extend(p.datatype.to_bytes(value))
                        req_keys.append(key)
                    else:
                        self.log.info('parameter %s not found', key)

                response_message = self.com_wrapper.send(request_message)

                resp_key_values = dict.fromkeys(req_keys)
                line_ptr = 0
                i = 0
                while line_ptr < len(response_message) or i < len(req_keys):
                    ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
                    resp_key_values[req_keys[i]] = ret_hdr.ret_code
                    line_ptr += len(ret_hdr)
                    i += 1
                return resp_key_values
            else:
                self.log.fatal('SETPARAMETER function not found')
        else:
            self.log.info('connector %s not found', connector)

    def read_parameters(self, connector, param_keys):
        c = self.get_connector(connector)
        if c is not None:
            f = c.get_function('GETPARAMETER')
            if f is not None:
                request_message = bytearray()
                req_keys = []
                req_params = []
                for key in param_keys:
                    p = c.get_parameter(key)
                    if p is not None:
                        request_message.extend(RPCFuncHdr(c.uid, f.uid, f.num_of_args()).to_bytes())
                        request_message.extend(self.get_datatype('UINT16').to_bytes(p.uid))
                        req_keys.append(key)
                        req_params.append(p)
                    else:
                        self.log.info('parameter %s not found', key)

                response_message = self.com_wrapper.send(request_message)

                resp_key_values = dict.fromkeys(req_keys)
                line_ptr = 0
                i = 0
                while line_ptr < len(response_message) or i < len(req_keys):
                    ret_hdr = read_RPCRetHdr(response_message[line_ptr:])
                    line_ptr += len(ret_hdr)
                    if ret_hdr.ret_code == 0:
                        if p.datatype.has_variable_size():
                            # ToDO work on variable size by reading first byte
                            pass
                        else:
                            resp_key_values[req_keys[i]] = req_params[i].datatype.read_bytes(response_message[line_ptr:])
                            line_ptr += p.datatyp.size
                    i += 1
                return resp_key_values
            else:
                self.log.fatal('SETPARAMETER function not found')
        else:
            self.log.info('connector %s not found', connector)

    def add_events_subscriber(self, connector, event_keys, event_callback, event_duration):
        pass

    def reset(self):
        pass

    def __str__(self):
        return "ContikiNode " + self.interface
