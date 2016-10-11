from wishful_module_gitar.lib_gitar import SensorNode


class RPCNode(SensorNode):

    def __init__(self, mac_addr, ip_addr, interface, com_wrapper, auto_config=False):
        mod_name = 'ContikiNode.' + interface
        self.log = logging.getLogger(mod_name)
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.interface = interface
        self.com_wrapper = com_wrapper
        self.com_wrapper.set_rx_callback(self.__serial_rx_handler)
        time.sleep(5)
        self.__response_message = bytearray()
        self.sequence_number = 0
        if auto_config is True:
            # read params/events/measurements from sensor
            self.log.warning("Tobe implemented")
        else:
            self.params_id_dct = {}
            self.params_name_dct = {}
            self.measurements_id_dct = {}
            self.measurements_name_dct = {}
            self.events_id_dct = {}
            self.events_name_dct = {}
        pass

    def register_parameters(self, connector_module, param_defs):
        self.params_id_dct[connector_module] = {}
        self.params_name_dct[connector_module] = {}

    def write_parameters(self, connector_module, param_key_values):

        pass

    def read_parameters(self, connector_module, param_keys):
        pass

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

    def __serial_rx_handler(self, error, response_message):
        pass
