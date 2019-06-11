import wishful_framework as wishful_module
from wishful_module_gitar.lib_gitar import ProtocolConnector
from wishful_module_gitar.lib_sensor import SensorNodeFactory
from wishful_framework.classes import exceptions

import logging
import inspect


@wishful_module.build_module
class BaseConnectorModule(wishful_module.AgentModule):

    def __init__(self, **kwargs):
        super(BaseConnectorModule, self).__init__()
        self.log = logging.getLogger('Contiki Base Connector')
        self.node_factory = SensorNodeFactory()
        self.supported_interfaces = kwargs['SupportedInterfaces']
        self.protocol_attributes = kwargs['ControlAttributes']
        self.protocol_functions = kwargs['ControlFunctions']
        self.protocol_connectors = kwargs['ProtocolConnectors']

    @wishful_module.on_start()
    def start_contiki_connector(self):
        for iface in self.supported_interfaces:
            for connector_name, connector_id in self.protocol_connectors.items():
                node = self.node_factory.get_node(iface)
                connector = ProtocolConnector(connector_id, connector_name)
                node.add_connector(connector)
                self.node_factory.parse_control_attributes(self.protocol_attributes[connector_name], node, connector)
                self.node_factory.parse_control_functions(self.protocol_functions[connector_name], node, connector)

    @wishful_module.on_exit()
    def stop_contiki_connector(self):
        # TODO: add safe removal of connector modules
        pass

    def get_attr_by_key(self, node, attr_type, attr_key):
        attr = None
        for connector_name, connector_id in self.protocol_connectors.items():
            if attr_type == 'parameter':
                attr = node.get_parameter(connector_id, attr_key)
            elif attr_type == 'event':
                attr = node.get_event(connector_id, attr_key)
            elif attr_type == 'measurement':
                attr = node.get_measurement(connector_id, attr_key)
            if attr is not None:
                return attr
        if attr is None:
            self.log.info("Attr %s not found", attr_key)
        return None

    def create_attribute_list_from_keys(self, node, attr_key_list, attr_type):
        if node is not None:
            attr_list = []
            for key in attr_key_list:
                attr = self.get_attr_by_key(node, attr_type, key)
                if attr is not None:
                    attr_list.append(attr)
            return attr_list
        self.log.fatal("%s Interface does not exist!" % (self.interface))
        raise exceptions.InvalidArgumentException(err_msg="Interface does not exist")
        return None

    def set_parameter(self, parameter_name, parameter_value):
        param_key_values = {parameter_name: parameter_value}
        node = self.node_factory.get_node(self.interface)
        parameter_list = self.create_attribute_list_from_keys(node, param_key_values.keys(), "parameter")
        ret = node.set_parameters(parameter_list, param_key_values)
        print("<<< set_parameter >>>", ret)
        
        if type(ret) == dict:
            return ret[parameter_name]
        else:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("Error executing function %s: %s!" % (fname, ret))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg="Error executing function")

    def get_parameter(self, parameter_name):
        param_keys = [parameter_name]
        node = self.node_factory.get_node(self.interface)
        parameter_list = self.create_attribute_list_from_keys(node, param_keys, "parameter")
        ret = node.get_parameters(parameter_list)
        if type(ret) == dict:
            return ret[parameter_name]
        else:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("Error executing function %s: %s!" % (fname, ret))
            raise exceptions.UPIFunctionExecutionFailedException(func_name=fname, err_msg="Error executing function")
