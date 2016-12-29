import wishful_framework as wishful_module
from wishful_module_contikibase.base_connector_module import BaseConnectorModule


__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2016, Universiteit Gent, IBCN, iMinds"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@intec.ugent.be"


@wishful_module.build_module
class GenericConnector(BaseConnectorModule):

    def __init__(self, **kwargs):
        super(GenericConnector, self).__init__(**kwargs)
