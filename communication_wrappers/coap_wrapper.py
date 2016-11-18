import logging
#from coapthon.client.helperclient import HelperClient
from communication_wrappers.lib_communication_wrapper import CommunicationWrapper


class CoAPWrapper(CommunicationWrapper):

    def __init__(self, ip_addr):
        self.log = logging.getLogger('CoAPWrapper.' + ip_addr)
        self.ip_addr = ip_addr

    def send(self, payload):
        #client = HelperClient(server=(self.ip_addr,5683))
        #response = client.post("wishful_funcs", payload)
        #client.stop()
        #return response.payload
        return "bla"
