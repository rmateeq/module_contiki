import wishful_upis as upis
import wishful_framework as wishful_module
from wishful_framework.classes import exceptions

import inspect
import traceback
import sys
import gevent
import _thread as thread

from .base_connector_module import BaseConnectorModule


@wishful_module.build_module
class NetConnectorModule(BaseConnectorModule):

    def __init__(self, **kwargs):
        super(NetConnectorModule, self).__init__(**kwargs)

    @wishful_module.bind_function(upis.net.set_parameters_net)
    def set_net_parameter(self, param_key_values_dict):
        node = self.node_factory.get_node(self.interface)
        try:
            param_list = self.create_attribute_list_from_keys(node, param_key_values_dict.keys(), "parameter")
            return node.set_parameters(param_list, param_key_values_dict)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.net.get_parameters_net)
    def get_net_parameters(self, param_key_list):
        node = self.node_factory.get_node(self.interface)
        try:
            param_list = self.create_attribute_list_from_keys(node, param_key_list, "parameter")
            return node.get_parameters(param_list)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.net.get_measurements_net)
    def get_net_measurements(self, measurement_key_list):
        node = self.node_factory.get_node(self.interface)
        try:
            measurement_list = self.create_attribute_list_from_keys(node, measurement_key_list, "measurement")
            return node.read_measurements(measurement_list)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    def get_net_measurements_periodic_worker(self, node, measurement_list, collect_period, report_period, num_iterations, report_callback):
        num_collects_report = report_period / collect_period
        for i in range(0, int(num_iterations)):
            measurement_report = {}
            for measurement in measurement_list:
                measurement_report[measurement.name] = []
            for i in range(0, int(num_collects_report)):
                gevent.sleep(collect_period)
                ret = node.read_measurements(measurement_list)
                for key in ret.keys():
                    measurement_report[key].append(ret[key])
            report_callback(node.interface, measurement_report)
        pass

    @wishful_module.bind_function(upis.net.get_measurements_periodic_net)
    def get_net_measurements_periodic(self, measurement_key_list, collect_period, report_period, num_iterations, report_callback):
        node = self.node_factory.get_node(self.interface)
        try:
            measurement_list = self.create_attribute_list_from_keys(node, measurement_key_list, "measurement")
            thread.start_new_thread(self.get_net_measurements_periodic_worker, (node, measurement_list, collect_period, report_period, num_iterations, report_callback,))
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.net.subscribe_events_net)
    def define_net_event(self, event_key_list, event_callback, event_duration):
        node = self.node_factory.get_node(self.interface)
        try:
            event_list = self.create_attribute_list_from_keys(node, event_key_list, "event")
            return node.subscribe_events(event_list, event_callback, event_duration)
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.net.get_network_info)
    def get_network_info(self):
        node = self.node_factory.get_node(self.interface)
        if node is not None:
            return NetworkInfo(self.node.ip_addr, node.params_name_dct['rime'].keys(), node.measurements_name_dct['rime'].keys(), node.events_name_dct['rime'].keys())
        else:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("%s Interface %s does not exist!" % (self.interface, fname))
            raise exceptions.InvalidArgumentException(func_name=fname, err_msg="Interface does not exist")

    @wishful_module.bind_function(upis.net.get_iface_ip_addr)
    def get_ipaddr(self):
        node = self.node_factory.get_node(self.interface)
        return node.ip_addr
