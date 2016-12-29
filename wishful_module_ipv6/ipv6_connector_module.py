import wishful_framework as wishful_module
from wishful_module_contikibase.net_connector_module import NetConnectorModule


@wishful_module.build_module
class IPv6Connector(NetConnectorModule):

    def __init__(self, **kwargs):
        super(IPv6Connector, self).__init__(**kwargs)
