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
class RadioConnectorModule(BaseConnectorModule):

    def __init__(self, **kwargs):
        super(RadioConnectorModule, self).__init__(**kwargs)

    @wishful_module.bind_function(upis.radio.set_parameters)
    def set_radio_parameter(self, param_key_values_dict):
        node = self.node_factory.get_node(self.interface)
        try:
            param_list = self.create_attribute_list_from_keys(node, param_key_values_dict.keys(), "parameter")
            return node.set_parameters(param_list, param_key_values_dict)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_parameters)
    def get_radio_parameters(self, param_key_list):
        node = self.node_factory.get_node(self.interface)
        try:
            param_list = self.create_attribute_list_from_keys(node, param_key_list, "parameter")
            return node.get_parameters(param_list)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_measurements)
    def get_radio_measurements(self, measurement_key_list):
        node = self.node_factory.get_node(self.interface)
        try:
            measurement_list = self.create_attribute_list_from_keys(node, measurement_key_list, "measurement")
            return node.read_measurements(measurement_list)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    def get_radio_measurements_periodic_worker(self, node, measurement_list, collect_period, report_period, num_iterations, report_callback):
        num_collects_report = report_period / collect_period
        for i in range(0, int(num_iterations)):
            measurement_report = {}
            for measurement in measurement_list:
                measurement_report[measurement.name] = []
            for j in range(0, int(num_collects_report)):
                gevent.sleep(collect_period)
                ret = node.read_measurements(measurement_list)
                for key in ret.keys():
                    measurement_report[key].append(ret[key])
            report_callback(node.interface, measurement_report)
        pass

    @wishful_module.bind_function(upis.radio.get_measurements_periodic)
    def get_radio_measurements_periodic(self, measurement_key_list, collect_period, report_period, num_iterations, report_callback):
        node = self.node_factory.get_node(self.interface)
        try:
            measurement_list = self.create_attribute_list_from_keys(node, measurement_key_list, "measurement")
            thread.start_new_thread(self.get_radio_measurements_periodic_worker, (node, measurement_list, collect_period, report_period, num_iterations, report_callback,))
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.subscribe_events)
    def define_radio_event(self, event_key_list, event_callback, event_duration):
        node = self.node_factory.get_node(self.interface)
        try:
            event_list = self.create_attribute_list_from_keys(node, event_key_list, "event")
            return node.subscribe_events(event_list, event_callback, event_duration)
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_hwaddr)
    def get_hwaddr(self):
        try:
            return self.get_parameter('IEEE802154_macShortAddress')
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.set_tx_power)
    def set_txpower(self, power_dBm):
        try:
            return self.set_parameter('IEEE802154_phyTXPower', power_dBm)
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_tx_power)
    def get_txpower(self):
        try:
            return self.get_parameter('IEEE802154_phyTXPower')
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.set_rxchannel)
    def set_rxchannel(self, freq_Hz, bandwidth):
        try:
            return self.set_parameter('IEEE802154_phyCurrentChannel', freq_Hz)
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_rxchannel)
    def get_rxchannel(self):
        try:
            return self.get_parameter('IEEE802154_phyCurrentChannel')
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.set_txchannel)
    def set_txchannel(self, freq_Hz, bandwidth):
        try:
            return self.set_parameter('IEEE802154_phyCurrentChannel', freq_Hz)
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_txchannel)
    def get_txchannel(self):
        try:
            return self.get_parameter('IEEE802154_phyCurrentChannel')
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_radio_info)
    def get_radio_info(self):
        node = self.node_factory.get_node(self.interface)
        if node is not None:
            return RadioInfo(node.mac_addr, node.params_name_dct['CONTIKIMAC'].keys(), node.measurements_name_dct['CONTIKIMAC'].keys(), node.events_name_dct['CONTIKIMAC'].keys(), ['CONTIKIMAC'])
        else:
            fname = inspect.currentframe().f_code.co_name
            self.log.fatal("%s Interface %s does not exist!" %
                           (self.interface, fname))
            raise exceptions.InvalidArgumentException(
                func_name=fname, err_msg="Interface does not exist")

    @wishful_module.bind_function(upis.radio.get_radio_platforms)
    def get_radio_platform(self):
        # retList = []
        # for interface in self.supported_interfaces:
        #    retList.append(RadioPlatform(interface, "TAISC"))
        # return retList
        return self.supported_interfaces
