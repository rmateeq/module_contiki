from wishful_module_gitar.lib_gitar import SensorNode, SensorDataType, SensorParameter, SensorFunction, SensorConnector
from communication_wrappers.lib_rpc import func_hdr_t, read_ret_header

import logging


class RPCNode(SensorNode):

    def __init__(self, node_uid, interface, mac_addr, ip_addr, com_wrapper):
        mod_name = 'ContikiNode.' + interface
        self.log = logging.getLogger(mod_name)
        self.node_uid = node_uid
        self.interface = interface
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.com_wrapper = com_wrapper
        self.datatypesIDs = {}
        self.datatypes = []
        self.connectorsIDs = {}
        self.connectors = []

    def register_datatypes(self, datatype_defs):
        for datatype_def in datatype_defs:
            datatype = SensorDataType(int(datatype_def['unique_id']),datatype_def['unique_name'],int(datatype_def['size']),datatype_def['format'],datatype_def['endianness'])
            self.datatypesIDs[datatype.name] = datatype.uid
            self.datatypes[datatype.uid] = datatype

    def num_of_datatypes(self):
        return len(self.datatypes)

    def get_datatype_uid(self, datatype_name):
        return self.datatypesIDs[datatype_name]

    def get_datatype(self, datatype_name):
        return self.datatypes[self.datatypesIDs[datatype_name]]

    def register_connectors(self, con_defs):
        for con_def in con_defs:
            con = SensorConnector(int(con_def['unique_id']), con_def['unique_name'])
            self.connectorsIDs[con.name] = con.uid
            self.connectors[con.uid] = con

    def num_of_connectors(self):
        return len(self.connectors)

    def get_connector_uid(self, con_name):
        return self.connectorsIDs[con_name]

    def get_connector(self, con_name):
        return self.connectors[self.connectorsIDs[con_name]]

    def register_parameters(self, connector_module, param_defs):
        con = self.get_connector(connector_module)
        for param_def in param_defs:
            datatype = self.get_datatype(param_def['datatype'])
            param = SensorParameter(int(param_def['unique_id']), param_def['unique_name'], datatype)
            con.add_parameter(param)

    def register_funcs(self, connector_module, func_defs):
        con = self.get_connector(connector_module)
        for func_def in func_defs:
            args_types_names = func_def['args_datatypes'].split(",")
            args_datatypes = []
            for arg_type_name in args_types_names:
                datatype = self.get_datatype(arg_type_name)
                args_datatypes.append(datatype)
            ret_datatype = self.get_datatype(func_def['ret_datatype'])
            func = SensorFunction(int(func_def['unique_id']),func_def['unique_name'], args_datatypes, ret_datatype)
            con.add_function(func)

    def write_parameters(self, connector_module, param_key_values):
        con = self.get_connector(connector_module)
        func = con.get_function("SETPARAMETER")
        message = bytearray()
        params = []
        for key,value in param_key_values:
            message.extend(func_hdr_t(con.uid, func.uid, func.num_of_args()))
            p = con.get_parameter(key)
            params.append(p)
            message.extend(self.get_datatype("UINT16").to_bin(p.uid))
            if p.has_variable_size():
                message.extend(len(value))
            message.extend(p.datatype.to_bin(value))
        
        response_message = self.com_wrapper.send(message)
        resp_key_values = {}
        line_ptr = 0
        i = 0
        while line_ptr < len(response_message) and i < len(params):
            ret_hdr = read_ret_header(response_message[line_ptr:])
            resp_key_values[params[i].name] = ret_hdr.ret_code
            line_ptr += len(ret_hdr)
            i += 1
        return resp_key_values

    def read_parameters(self, connector_module, param_keys):
        con = self.get_connector(connector_module)
        func = con.get_function("GETPARAMETER")
        message = bytearray()
        params = []
        for key in param_keys:
            message.extend(func_hdr_t(con.uid, func.uid, func.num_of_args()))
            p = con.get_parameter(key)
            params.append(p)
            message.extend(self.get_datatype("UINT16").to_bin(p.uid))

        response_message = self.com_wrapper.send(message)
        resp_key_values = {}
        line_ptr = 0
        i = 0
        while line_ptr < len(response_message) or i < len(params):
            ret_hdr = read_ret_header(response_message[line_ptr:])
            line_ptr += len(ret_hdr)

            if p.has_variable_size():
                value_length = self.get_datatype("UINT8").from_bin(response_message[line_ptr:])
                line_ptr += 1
                resp_key_values[params[i].name] = params[i].datatype.from_bin(response_message[line_ptr:], value_length)
                line_ptr += value_length
            else:
                resp_key_values[params[i].name] = params[i].datatype.from_bin(response_message[line_ptr:])
                line_ptr += p.datatyp.size

            i += 1
        return resp_key_values

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
