import logging
from coapthon.client.helperclient import HelperClient
from communication_wrappers.lib_communication_wrapper import CommunicationWrapper
import subprocess
import threading
import aiocoap
import asyncio


class CoAPWrapper(CommunicationWrapper):

    def __init__(self, ip_addr, node_id, serial_dev):
        self.log = logging.getLogger('CoAPWrapper.' + ip_addr)
        self.ip_addr = ip_addr
        self.node_id = node_id
        self.control_prefix = "fd00:c:" + str(node_id) + "::"
        control_tunslip_interface_id = "1"
        prefix_length = "/64"
        tunslip_ip_addr = self.control_prefix + control_tunslip_interface_id + prefix_length
        cmd = 'sudo ../../agent_modules/contiki/communication_wrappers/bin/tunslip6 -C -s ' + serial_dev + ' ' + tunslip_ip_addr
        self.log.info(cmd)
        self.slip_process = subprocess.Popen(['sudo', '../../agent_modules/contiki/communication_wrappers/bin/tunslip6', '-C', '-s' + serial_dev, tunslip_ip_addr], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.__thread_stop = threading.Event()
        self.__rx_thread = threading.Thread(target=self.__serial_listen, args=(self.__thread_stop,))
        self.__rx_thread.daemon = True
        self.__rx_thread.start()
        self.__response = None

    @asyncio.coroutine
    def coap_send(self, payload):
        context = yield from aiocoap.Context.create_client_context()
        request = aiocoap.Message(code=aiocoap.POST, payload=payload)
        request.set_request_uri('coap://[' + self.control_prefix + '2]/wishful_funcs')
        response = yield from context.request(request).response
        self.log.info("Result: %s\n%r" % (response.code, response.payload))
        self.__response = response.payload

    def send(self, payload):
        if True:
            asyncio.get_event_loop().run_until_complete(self.coap_send(payload))
            return self.__response
        else:
            client = HelperClient(server=(self.control_prefix + "2", 5683))
            response = client.post("wishful_funcs", payload)
            client.stop()
            return response.payload

    def __serial_listen(self, stop_event):
        while not stop_event.is_set():
            self.log.info("%s", self.slip_process.stdout.readline().strip())
