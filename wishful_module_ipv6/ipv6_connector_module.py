import wishful_framework as wishful_module
import wishful_upis as upis
from wishful_module_contikibase.net_connector_module import NetConnectorModule
import traceback
import sys


@wishful_module.build_module
class IPv6Connector(NetConnectorModule):

    def __init__(self, **kwargs):
        super(IPv6Connector, self).__init__(**kwargs)

    @wishful_module.bind_function(upis.net.rpl_set_border_router)
    def rpl_set_border_router(self, rpl_prefix):
        node = self.node_factory.get_node(self.interface)
        try:
            return node.forward_rpc("rpl_connector", "rpl_set_border_router", rpl_prefix)
        except Exception:
            traceback.print_exc(file=sys.stdout)
