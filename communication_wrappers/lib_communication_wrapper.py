import abc

class CommunicationWrapper():
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def send(payload):
        return
    
    @abc.abstractmethod
    def set_rx_callback(rx_callback):
        return
