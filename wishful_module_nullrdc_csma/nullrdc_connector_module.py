import wishful_upis as upis
import wishful_framework as wishful_module

import traceback
import sys

from wishful_module_contikibase.radio_connector_module import RadioConnectorModule


@wishful_module.build_module
class NULLRDCConnector(RadioConnectorModule):

    def __init__(self, **kwargs):
        super(NULLRDCConnector, self).__init__(**kwargs)

    @wishful_module.bind_function(upis.radio.get_running_radio_program)
    def get_active(self):
        try:
            return "CONTIKIMAC"
        except Exception:
            traceback.print_exc(file=sys.stdout)
