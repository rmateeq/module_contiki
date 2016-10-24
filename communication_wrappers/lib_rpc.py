import errno
import struct
from ctypes import *


class func_hdr_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("connector_id",c_uint8),("func_id",c_uint16),("num_of_args",c_uint8)]

    fmt_func_header = struct.Struct("<BHB")

    def __repr__(self):
        return "(C:%s,F:%s,NoA:%d)" % (self.connector_id,self.func_id,self.num_of_args)


def read_func_header(message):
    connector_id,func_id,num_of_args = fmt_func_header.unpack_from(message)
    return func_hdr_t(connector_id,func_id,num_of_args)


def printRetCode(ret_code):
    if ret_code == 0:
        return "SUCCESS"
    elif ret_code in errno.errorcode:
        return errno.errorcode[ret_code]
    else:
        return "CODE NOT SUPPORTED"


class ret_hdr_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("connector_id",c_uint8),("func_id",c_uint16),("ret_type",c_uint8),("ret_code",c_int8)]

    fmt_ret_header = struct.Struct("<BHBB")

    def __repr__(self):
        return "(C:%s,F:%s,RT:%s,RC:%s)" % (self.connector_id, self.func_id, self.ret_type, printRetCode(self.ret_code))


def read_ret_header(message):
    connector_id,func_id,ret_type,ret_code = fmt_ret_header.unpack_from(message)
    return ret_hdr_t(connector_id,func_id,ret_type,ret_code)
