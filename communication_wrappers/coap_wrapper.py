import logging
# from coapthon.client.helperclient import HelperClient
from communication_wrappers.lib_communication_wrapper import CommunicationWrapper
import subprocess
import threading

import asyncio
import aiocoap
import aiocoap.resource as resource
import gevent


class CoAPWrapper(CommunicationWrapper):

    def __init__(self, node_id, serial_dev, serial_baudrate, serial_delay="0"):
        self.node_id = node_id
        self.control_prefix = "fd00:c:" + str(node_id) + "::"
        # self.control_prefix = "fd00:c::"
        control_tunslip_interface_id = "1"
        prefix_length = "/64"
        tunslip_ip_addr = self.control_prefix + control_tunslip_interface_id + prefix_length
        self.log = logging.getLogger('CoAPWrapper.' + str(self.node_id))

        if int(subprocess.check_output("sudo ip6tables -C INPUT -d " + tunslip_ip_addr + " -j ACCEPT 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -I INPUT 1 -d " + tunslip_ip_addr + " -j ACCEPT", shell=True, universal_newlines=True).strip()

        if int(subprocess.check_output("sudo ip6tables -C OUTPUT -s " + tunslip_ip_addr + " -j ACCEPT 2> /dev/null; echo $?", shell=True, universal_newlines=True).strip()) > 0:
            subprocess.check_output("sudo ip6tables -I OUTPUT 1 -s " + tunslip_ip_addr + " -j ACCEPT", shell=True, universal_newlines=True).strip()

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
            # self.slip_process = subprocess.Popen(['sudo', '../../agent_modules/contiki/communication_wrappers/bin/tunslip6', '-v5', '-D' + serial_delay, '-B', serial_baudrate, '-C', '-s' + serial_dev, tunslip_ip_addr], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.__thread_stop = threading.Event()
        self.__rx_thread = threading.Thread(target=self.__serial_listen, args=(self.__thread_stop,))
        self.__rx_thread.daemon = True
        self.__rx_thread.start()
        self.__response = None
        self.event_cb = None
        self.event_loop = asyncio.new_event_loop()
        __event_thread = threading.Thread(target=self.__event_server, args=(self, "fd00:c:" + str(node_id) + "::1", 5683))
        __event_thread.daemon = True
        __event_thread.start()

    @asyncio.coroutine
    def coap_send(self, send_loop, payload):
        asyncio.set_event_loop(send_loop)
        context = yield from aiocoap.Context.create_client_context()
        request = aiocoap.Message(code=aiocoap.POST, payload=payload)
        request.set_request_uri('coap://[' + self.control_prefix + '2]/wishful_funcs')
        response = yield from context.request(request).response
        # self.log.info("Result: %s\n%s\n%r" % (response.code, response, response.payload))
        self.__response = response.payload
        yield from context.shutdown()

    def send(self, payload):
        if True:
            send_loop = asyncio.new_event_loop()
            # __event_thread = threading.Thread(target=self.async_send, args=(payload,))
            # __event_thread.start()
            # __event_thread.join()
            # # send_task = asyncio.async(self.coap_send(payload))
            # yield from asyncio.wait_for(send_task)
            send_loop.run_until_complete(self.coap_send(send_loop, payload))
            # asyncio.get_event_loop().run_until_complete(self.coap_send(payload))
            # while self.__response is None:
            #     gevent.sleep(0.1)
            return self.__response
        # else:
        #     client = HelperClient(server=(self.control_prefix + "2", 5683))
        #     response = client.post("wishful_funcs", payload)
        #     client.stop()
        #     return response.payload

    def __serial_listen(self, stop_event):
        while not stop_event.is_set():
            self.log.info("%s", self.slip_process.stdout.readline().strip())

    @asyncio.coroutine
    def coap_event_server(self, comm_wrapper, ip6_address, coap_port):
        root = resource.Site()
        root.add_resource(('.well-known', 'core'), resource.WKCResource(root.get_resources_as_linkheader))
        root.add_resource(('wishful_events',), EventResource(comm_wrapper))
        yield from aiocoap.Context.create_server_context(root, bind=(ip6_address, coap_port))

    def __event_server(self, comm_wrapper, ip6_address, coap_port):
        asyncio.set_event_loop(self.event_loop)
        gevent.sleep(5)
        send_task = asyncio.async(self.coap_event_server(comm_wrapper, ip6_address, coap_port), loop=self.event_loop)
        print(send_task)
        try:
            while self.event_loop.is_running():
                gevent.sleep(1)
            else:
                self.event_loop.run_forever()
        finally:
            print("ended")
            self.event_loop.close()

    def add_event_callback(self, cb):
        self.event_cb = cb


class EventResource(resource.Resource):
    """
    Example resource which supports GET and PUT methods. It sends large
    responses, which trigger blockwise transfer.
    """

    def __init__(self, comm_wrapper):
        super(EventResource, self).__init__()
        self.comm_wrapper = comm_wrapper

    @asyncio.coroutine
    def render_post(self, request):
        content = request.payload
        # print("Event from {}, payload {}".format(request.remote.sockaddr[0], content))
        if self.comm_wrapper.event_cb is not None:
            self.comm_wrapper.event_cb(content)
        response = aiocoap.Message(code=aiocoap.EMPTY, payload="")
        return response
