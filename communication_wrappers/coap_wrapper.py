import logging
# from coapthon.client.helperclient import HelperClient
from communication_wrappers.lib_communication_wrapper import CommunicationWrapper
import subprocess
import threading

import asyncio
import aiocoap
# import aiocoap.resource as resource


class CoAPWrapper(CommunicationWrapper):

    def __init__(self, node_id, serial_dev, serial_baudrate, serial_delay="0"):
        self.node_id = node_id
        self.control_prefix = "fd00:c:" + str(node_id) + "::"
        # self.control_prefix = "fd00:c::"
        control_tunslip_interface_id = "1"
        prefix_length = "/64"
        tunslip_ip_addr = self.control_prefix + control_tunslip_interface_id + prefix_length
        self.log = logging.getLogger('CoAPWrapper.' + str(self.node_id))

        if int(subprocess.check_output("sudo ip6tables -C INPUT -d fd00:c::/24 -j ACCEPT 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -A INPUT -d fd00:c::/24 -j ACCEPT", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo ip6tables -C OUTPUT -s fd00:c::/24 -j ACCEPT 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -A OUTPUT -s fd00:c::/24 -j ACCEPT", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo ip6tables -C OUTPUT -o tun+ -j DROP 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -A OUTPUT -o tun+ -j DROP", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo ip6tables -C FORWARD -o tun+ -j DROP 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -A FORWARD -o tun+ -j DROP", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo ip6tables -C FORWARD -i tun+ -j DROP 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -A FORWARD -i tun+ -j DROP", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo iptables -C OUTPUT -o tun+ -j DROP 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo iptables -A OUTPUT -o tun+ -j DROP", shell=True, universal_newlines=True).strip()

        if "cooja" in serial_dev:
            cmd = 'sudo ../../agent_modules/contiki/communication_wrappers/bin/tunslip6-cooja -C -D' + serial_delay + ' -B ' + serial_baudrate + ' -s ' + serial_dev + ' ' + tunslip_ip_addr
            self.log.info(cmd)
            self.slip_process = subprocess.Popen(['sudo', '../../agent_modules/contiki/communication_wrappers/bin/tunslip6-cooja', '-D' + serial_delay, '-B', serial_baudrate, '-C', '-s' + serial_dev, tunslip_ip_addr], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        else:
            cmd = 'sudo ../../agent_modules/contiki/communication_wrappers/bin/tunslip6 -C -B ' + serial_baudrate + ' -s ' + serial_dev + ' ' + tunslip_ip_addr
            self.log.info(cmd)
            self.slip_process = subprocess.Popen(['sudo', '../../agent_modules/contiki/communication_wrappers/bin/tunslip6', '-D' + serial_delay, '-B', serial_baudrate, '-C', '-s' + serial_dev, tunslip_ip_addr], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.__thread_stop = threading.Event()
        self.__rx_thread = threading.Thread(target=self.__serial_listen, args=(self.__thread_stop,))
        self.__rx_thread.daemon = True
        self.__rx_thread.start()
        self.__response = None
        # root = resource.Site()
        # root.add_resource(('.well-known', 'core'), resource.WKCResource(root.get_resources_as_linkheader))
        # root.add_resource(('wishful_events',), EventResource())
        # asyncio.Task(aiocoap.Context.create_server_context(root))
        # asyncio.get_event_loop().run_forever()

    @asyncio.coroutine
    def coap_send(self, payload):
        context = yield from aiocoap.Context.create_client_context()
        request = aiocoap.Message(code=aiocoap.POST, payload=payload)
        request.set_request_uri('coap://[' + self.control_prefix + '2]/wishful_funcs')
        response = yield from context.request(request).response
        # self.log.info("Result: %s\n%r" % (response.code, response.payload))
        self.__response = response.payload
        yield from context.shutdown()

    def send(self, payload):
        if True:
            asyncio.get_event_loop().run_until_complete(self.coap_send(payload))
            return self.__response
        # else:
        #     client = HelperClient(server=(self.control_prefix + "2", 5683))
        #     response = client.post("wishful_funcs", payload)
        #     client.stop()
        #     return response.payload

    def __serial_listen(self, stop_event):
        while not stop_event.is_set():
            self.log.info("%s", self.slip_process.stdout.readline().strip())


# class EventResource(resource.Resource):
#     """
#     Example resource which supports GET and PUT methods. It sends large
#     responses, which trigger blockwise transfer.
#     """

#     def __init__(self):
#         super(EventResource, self).__init__()

#     async def render_get(self, request):
#         return aiocoap.Message(payload=self.content)

#     async def render_put(self, request):
#         print('PUT payload: %s' % request.payload)
#         self.content = request.payload
#         payload = ("I've accepted the new payload. You may inspect it here in "\
#                 "Python's repr format:\n\n%r"%self.content).encode('utf8')
#         return aiocoap.Message(payload=payload)
