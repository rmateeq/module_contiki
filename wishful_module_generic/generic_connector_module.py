import wishful_framework as wishful_module
import wishful_upis as upis
import traceback
import sys
from wishful_module_contikibase.base_connector_module import BaseConnectorModule


__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2016, Universiteit Gent, IBCN, iMinds"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@intec.ugent.be"


@wishful_module.build_module
class GenericConnector(BaseConnectorModule):

    def __init__(self, **kwargs):
        super(GenericConnector, self).__init__(**kwargs)

    @wishful_module.bind_function(upis.mgmt.disseminate_radio_program)
    def disseminate_radio_program(self, radio_program_id, radio_program, nodes, source_node=0):
        """This function allows to disseminate radio programs to one or more nodes.
        Optionally, a source node can be selected that manages the dissemination process.

        Args:
            radio_program_id (int): Radio program identifier.
            radio_program (file): Binary file containing radio program.
            nodes (list[int]): List of node IDs that need to receive the update.
            source_node (int, optional): ID of the node that manages the dissemination process.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        return -1

    @wishful_module.bind_function(upis.mgmt.inject_radio_program)
    def inject_radio_program(self, radio_program_id, nodes, source_node=0):
        """This function allows to inject a previously disseminated radio programs in one or more nodes.
        Optionally, a source node can be selected that manages the injection process.

        Args:
            radio_program_id (int): Radio program identifier.
            nodes (list[int]): List of node IDs that need to inject the radio program.
            source_node (int, optional): ID of the node that manages the injection process.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        return -1

    @wishful_module.bind_function(upis.mgmt.prepare_ota_update)
    def prepare_ota_update(self, nodes=[]):
        node = self.node_factory.get_node(self.interface)
        try:
            return node.allocate_memory(nodes)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.allocate_memory)
    def allocate_memory(self, elf_file_size, rom_size, ram_size):
        """This function allocates memory on one or more nodes.
        The allocated memory will be used to store the software module and/or radio program.
        This step is required when using an offline ELF linker because the exact memory location must be known upfront.

        Args:
            elf_file_size (int): Size of the ELF file that needs to be stored.
            rom_size (int): ROM usage of the code contained in the ELF file.
            ram_size (int): RAM usage of the code contained in the ELF file.

        Returns:
            AllocatedMemoryBlock: Returns the allocated ROM and RAM addressess, repeats the sizes.
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.allocate_memory(elf_file_size, rom_size, ram_size)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.store_file)
    def store_file(self, is_last_block, block_size, block_offset, block_data):
        """This function allows disseminating a software module (i.e. ELF object file) to one or more nodes.

        Args:
            elf_object_file_id (int): ELF object file identifier
            elf_object_file (file): ELF object file
            nodes (list[int]): List of node IDs that need to receive the ELF file.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        # first we need to store the ELF object file on the node
        # for this purpose we need to divide the file in chunks and send the chunks one by one
        try:
            return node.store_file(is_last_block, block_size, block_offset, block_data)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.disseminate_software_module)
    def disseminate_software_module(self):
        """This function allows disseminating a software module (i.e. ELF object file) to one or more nodes.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.disseminate_file()
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.install_software_module)
    def install_software_module(self):
        """This function allows installing a previously disseminated software module on one or more nodes.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.install_module()
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.activate_software_module)
    def activate_software_module(self):
        """This function allows activating a previously installed software module on one or more nodes.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.activate_module()
        except Exception:
            traceback.print_exc(file=sys.stdout)
