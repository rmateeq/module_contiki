import errno
import struct
from ctypes import *
from enum import IntEnum
from tlv import *

class RPC_CONNECTORS(IntEnum):
    CROSS_LAYER_CONNECTOR = 0
    IPV6_CONNECTOR = 1


connectors = {
    RPC_CONNECTORS.CROSS_LAYER_CONNECTOR: 'CROSS_LAYER',
    RPC_CONNECTORS.IPV6_CONNECTOR: 'IPv6'
}

class RPC_FUNCTIONS(IntEnum):
    SETPARAMETER = 0
    GETPARAMETER = 1
    SUBSCRIBEEVENT = 2
    UNSUBSCRIBEEVENT = 3
    GETMEASUREMENT = 4
    GETMEASUREMENTBOUNCE = 5
    SETACTIVE = 6
    GETACTIVE = 7
    SETINACTIVE = 8
    GETNETWORKINFO = 9
    GETIPTABLE = 10,
    CLEARIPTABLE = 11


rpc_funtions = {
    RPC_FUNCTIONS.SETPARAMETER:'SETPARAMETER',
    RPC_FUNCTIONS.GETPARAMETER:'GETPARAMETER',
    RPC_FUNCTIONS.SUBSCRIBEEVENT:'SUBSCRIBEEVENT',
    RPC_FUNCTIONS.UNSUBSCRIBEEVENT:'UNSUBSCRIBEEVENT',
    RPC_FUNCTIONS.GETMEASUREMENT:'GETMEASUREMENT',
    RPC_FUNCTIONS.GETMEASUREMENTBOUNCE:'GETMEASUREMENTBOUNCE',
    RPC_FUNCTIONS.SETACTIVE:'SETACTIVE',
    RPC_FUNCTIONS.GETACTIVE:'GETACTIVE',
    RPC_FUNCTIONS.SETINACTIVE:'SETINACTIVE',
    RPC_FUNCTIONS.GETNETWORKINFO:'GETNETWORKINFO',
    RPC_FUNCTIONS.GETIPTABLE:'GETIPTABLE',
    RPC_FUNCTIONS.CLEARIPTABLE:'CLEARIPTABLE',
}

def printRetCode(ret_code):
    if ret_code == 0:
        return "SUCCESS"
    elif ret_code in errno.errorcode:
        return errno.errorcode[ret_code]
    else:
        return "CODE NOT SUPPORTED"

class SensorParameter():
    def __init__(self, uname, uid, type_name, type_len=None, type_format="", type_subformat=""):
        self.unique_name = uname
        self.unique_id = uid
        self.tlv = TLV(t=types_names[type_name], l=type_len)


class func_hdr_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("connector_id",c_uint8),("func_id",c_uint16),("num_of_args",c_uint8)]

    def toString(self):
        return "(C:%s,F:%s,NoA:%d)" % (connectors[self.connector_id],rpc_funtions[self.func_id],self.num_of_args)

def readFuncHeader(message):
    connector_id,func_id,num_of_args = struct.unpack_from("<BHB",message)
    return func_hdr_t(connector_id,func_id,num_of_args)

class ret_hdr_t(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [("connector_id",c_uint8),("func_id",c_uint16),("ret_type",c_uint8),("ret_code",c_int8)]

    def toString(self):
        return "(C:%s,F:%s,RT:%s,RC:%s)" % (connectors[self.connector_id],rpc_funtions[self.func_id],types[self.ret_type],printRetCode(self.ret_code))

def readRetHeader(message):
    connector_id,func_id,ret_type,ret_code = struct.unpack_from("<BHBB",message)
    return ret_hdr_t(connector_id,func_id,ret_type,ret_code)

def createRPCFunctionCall(connector_id,func_id,*args):
    args_bytes = bytearray()
    num_of_args = 0

    for tlv_arg in args:
        if isinstance(tlv_arg,TLV):
            num_of_args += 1
            args_bytes.extend(writeTLVBytesFromTLV(tlv_arg))
        else:
            print "Error reading arguments. Required format (connector_id,func_id,TLV(..),TLV(..),..."
            return

    func_hdr = func_hdr_t(connector_id,func_id,num_of_args)
    rpc_msg = bytearray(func_hdr)
    rpc_msg.extend(args_bytes)
    return rpc_msg


def printReqMsg(req_msg):
    req_index = 0
    req_msg_len = len(req_msg)

    while req_index < req_msg_len:
        fun_hdr = readFuncHeader(req_msg[req_index:])
        print fun_hdr.toString()
        req_index += sizeof(func_hdr_t)

        num_of_args = 0
        while num_of_args < fun_hdr.num_of_args:
            tlv_arg = readTLV(req_msg[req_index:])
            print "\t%s" % (tlv_arg.toString())
            known_len = known_lens[tlv_arg.t]
            if known_len == 0:
                req_index = req_index + 2 + tlv_arg.l
            else:
                req_index = req_index + 1 + tlv_arg.l
            num_of_args += 1


def printResponseMsg(resp_msg):
    resp_index = 0
    resp_msg_len = len(resp_msg)

    while resp_index < resp_msg_len:
        ret_hdr = readRetHeader(resp_msg[resp_index:])
        print ret_hdr.toString()
        resp_index += sizeof(ret_hdr_t)

        if ret_hdr.ret_type != TYPES.VOID_T and ret_hdr.ret_code == 0:
            tlv_data = readTLV(resp_msg[resp_index:])
            print "\t%s" % (tlv_data.toString())
            known_len = known_lens[tlv_data.t]
            if known_len == 0:
                resp_index += 2 + tlv_data.l
            else:
                resp_index += 1 + tlv_data.l


def printEventMsg(evt_msg):
    event_uid = struct.unpack("H",evt_msg[0:2])[0]
    print "(E:%u) " % (event_uid),
    tlv_data = readTLV(evt_msg[2:])
    print tlv_data.toString()
