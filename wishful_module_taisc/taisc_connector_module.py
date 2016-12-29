import wishful_upis as upis
import wishful_framework as wishful_module
from wishful_framework.classes import exceptions

import inspect
import traceback
import sys

from wishful_module_contikibase.radio_connector_module import RadioConnectorModule


@wishful_module.build_module
class TAISCConnector(RadioConnectorModule):

    def __init__(self, **kwargs):
        super(TAISCConnector, self).__init__(**kwargs)
        self.radio_programs = kwargs['RadioPrograms']
        self.radio_program_names = {}
        for rp_name in self.radio_programs.keys():
            self.radio_program_names[self.radio_programs[rp_name]] = rp_name

    @wishful_module.bind_function(upis.radio.activate_radio_program)
    def set_active(self, name):
        try:
            if name in self.radio_programs:
                return self.set_parameter('TAISC_ACTIVERADIOPROGRAM', self.radio_programs[name])
            else:
                fname = inspect.currentframe().f_code.co_name
                self.log.warn("Wrong radio program name: %s" % name)
                raise exceptions.InvalidArgumentException(func_name=fname, err_msg="Radio Program does not exist")
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.deactivate_radio_program)
    def set_inactive(self, name):
        try:
            if name in self.radio_programs:
                return self.set_parameter('TAISC_ACTIVERADIOPROGRAM', self.radio_programs['CSMA'])
            else:
                fname = inspect.currentframe().f_code.co_name
                self.log.warn("Wrong radio program name: %s" % name)
                raise exceptions.InvalidArgumentException(func_name=fname, err_msg="Radio Program does not exist")
        except:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.radio.get_running_radio_program)
    def get_active(self):
        try:
            return self.radio_program_names[self.get_parameter('TAISC_ACTIVERADIOPROGRAM')]
        except:
            traceback.print_exc(file=sys.stdout)
