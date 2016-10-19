from wishful_module_gitar.lib_gitar import SensorNode, SensorParameter
from wishful_module_gitar.sensorDataType import SensorDataType
from communication_wrappers.lib_rpc import SensorRPCFunc, read_ret_header
from communication_wrappers.lib_tlv import TLV, read_TLV_from_buf

import logging
import time


class RPCNode(SensorNode):

    def __init__(self, node_id, mac_addr, ip_addr, interface, com_wrapper, auto_config=False):
        mod_name = 'ContikiNode.' + interface
        self.log = logging.getLogger(mod_name)
        self.node_id = node_id
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.interface = interface
        self.com_wrapper = com_wrapper
        time.sleep(5)
        self.__response_message = bytearray()
        self.sequence_number = 0
        if auto_config is True:
            # read params/events/measurements from sensor
            self.log.warning("ToBe implemented")
        else:
            self.datatypes_id_dct = {}
            self.datatypes_name_dct = {}
            self.funcs_id_dct = {}
            self.funcs_name_dct = {}
            self.params_id_dct = {}
            self.params_name_dct = {}
            self.measurements_id_dct = {}
            self.measurements_name_dct = {}
            self.events_id_dct = {}
            self.events_name_dct = {}
        pass

    def register_datatypes(self, datatype_defs):
        for datatype_def in datatype_defs:
            datatype = SensorDataType(int(datatype_def['unique_id']),datatype_def['unique_name'],int(datatype_def['length']),datatype_def['endianness'],datatype_def['type_format'])
            self.datatypes_id_dct[int(datatype_def['unique_id'])] = datatype
            self.datatypes_name_dct[datatype_def['unique_name']] = datatype

    def register_funcs(self, connector_module, func_defs):
        self.funcs_id_dct[connector_module] = {}
        self.funcs_name_dct[connector_module] = {}
        for func_def in func_defs:
            func = SensorRPCFunc(int(func_def['unique_connector_id']),int(func_def['unique_id']),func_def['unique_name'],int(func_def['num_of_args']),func_def['args_types'],int(func_def['ret_type']))
            self.funcs_id_dct[connector_module][int(func_def['unique_id'])] = func
            self.funcs_name_dct[connector_module][func_def['unique_name']] = func

    def register_parameters(self, connector_module, param_defs):
        self.params_id_dct[connector_module] = {}
        self.params_name_dct[connector_module] = {}
        for param_def in param_defs:
            datatype = self.datatypes_name_dct[param_def['type_name']]
            param = SensorParameter(int(param_def['unique_id']), param_def['unique_name'], datatype)
            self.params_id_dct[connector_module][int(param_def['unique_id'])] = param
            self.params_name_dct[connector_module][param_def['unique_name']] = param

    def write_parameters(self, connector_module, param_key_values):
        message = bytearray()
        f = self.funcs_name_dct[connector_module]['SETPARAMETER']
        for key in param_key_values:
            if connector_module in self.params_name_dct and key in self.params_name_dct[connector_module]:
                p = self.params_name_dct[connector_module][key]
                param_uid_tlv = TLV(self.datatypes_name_dct['UINT_16'].uid, self.datatypes_name_dct['UINT_16'].length, p.uid)
                value_tlv = TLV(p.datatype.uid, p.datatype.length, param_key_values[key])
                message += f.to_bin(self.datatypes_id_dct,param_uid_tlv,value_tlv)
        
        response_message = self.com_wrapper.send(message)
        param_key_values = {}
        line_ptr = 0
        for key in param_key_values:
            ret_hdr = read_ret_header(response_message[line_ptr:])
            param_key_values[key] = ret_hdr.ret_code
            line_ptr += len(ret_hdr)
        return param_key_values

    def read_parameters(self, connector_module, param_keys):
        message = bytearray()
        f = self.funcs_name_dct[connector_module]['GETPARAMETER']
        for key in param_keys:
            if connector_module in self.params_name_dct and key in self.params_name_dct[connector_module]:
                p = self.params_name_dct[connector_module][key]
                param_uid_tlv = TLV(self.datatypes_name_dct['UINT_16'].uid, self.datatypes_name_dct['UINT_16'].length, p.uid)
                message += f.to_bin(self.datatypes_id_dct,param_uid_tlv)

        response_message = self.com_wrapper.send(message)
        param_key_values = {}
        line_ptr = 0
        for key in param_keys:
            ret_hdr = read_ret_header(response_message[line_ptr:])
            line_ptr += len(ret_hdr)
            if ret_hdr.ret_code == 0:
                ret_tlv = read_TLV_from_buf(self.datatypes_id_dct,response_message[line_ptr:])
                param_key_values[key] = ret_tlv.value
                if self.datatypes_id_dct[ret_tlv.type_uid].length == 0:
                    line_ptr += 1
                line_ptr += ret_tlv.length
        return param_key_values

    def register_measurements(self, connector_module, measurement_defs):
        pass

    def read_measurements(self, connector_module, measurement_keys):
        pass

    def register_events(self, connector_module, event_defs):
        pass

    def add_events_subscriber(self, connector_module, event_keys, event_callback, event_duration):
        pass

    def reset(self):
        pass

    def __str__(self):
        return "ContikiNode " + self.interface
