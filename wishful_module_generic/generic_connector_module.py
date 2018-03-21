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

    @wishful_module.bind_function(upis.mgmt.allocate_memory)
    def allocate_memory(self, module_id, elf_file_size, rom_size, ram_size, nodes=[]):
        """This function allocates memory on one or more nodes.
        The allocated memory will be used to store the software module and/or radio program.
        This step is required when using an offline ELF linker because the exact memory location must be known upfront.

        Args:
            elf_file_size (int): Size of the ELF file that needs to be stored.
            rom_size (int): ROM usage of the code contained in the ELF file.
            ram_size (int): RAM usage of the code contained in the ELF file.
            nodes (list[int]): List of node IDs that need to allocate_memory.

        Returns:
            AllocatedMemoryBlock: Returns the allocated ROM and RAM addressess, repeats the sizes.
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.allocate_memory(module_id, elf_file_size, rom_size, ram_size, nodes)
            # return node.forward_rpc("gitar_connector", "gitar_allocate_memory", rom_size, ram_size, text_offset, nodes)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.disseminate_software_module)
    def disseminate_software_module(self, module_id, elf_program_file, block_size=64, nodes=[]):
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
            block_index = 0
            block_offset = 0
            with open(elf_program_file, "rb") as binary_file:
                bin_string = binary_file.read()
                while len(bin_string) > block_size:
                    # err = node.forward_rpc("gitar_connector", "gitar_store_file", block_index, block_size, block_offset, bin_string[:block_size])
                    err = node.store_file(module_id, block_index, block_size, block_offset, bin_string[:block_size])
                    if err != 0:
                        print("Error storing block {}, offset {}, size {}".format(block_index, block_offset, block_size))
                    block_index += 1
                    block_offset += block_size
                    bin_string = bin_string[block_size:]
                # err = node.forward_rpc("gitar_connector", "gitar_store_file", block_index, len(bin_string), block_offset, bin_string)
                err = node.store_file(module_id, block_index, len(bin_string), block_offset, bin_string)
                if err != 0:
                    print("Error storing block {}, offset {}, size {}".format(block_index, block_offset, block_size))
            return node.disseminate_file(module_id, nodes)
            # return node.forward_rpc("gitar_connector", "gitar_disseminate_file", nodes)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.install_software_module)
    def install_software_module(self, module_id, nodes=[]):
        """This function allows installing a previously disseminated software module on one or more nodes.

        Args:
            elf_object_file_id (int): ELF object file identifier
            nodes (list[int]): List of node IDs that need to install the ELF file.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.install_module(module_id, nodes)
            # return node.forward_rpc("gitar_connector", "gitar_install_module", nodes)
        except Exception:
            traceback.print_exc(file=sys.stdout)

    @wishful_module.bind_function(upis.mgmt.activate_software_module)
    def activate_software_module(self, module_id, nodes=[]):
        """This function allows activating a previously installed software module on one or more nodes.

        Args:
            elf_object_file_id (int): ELF object file identifier
            nodes (list[int]): List of node IDs that need to activate the ELF file.

        Returns:
            int: Error value 0 = SUCCESS; -1 = FAIL
        """
        node = self.node_factory.get_node(self.interface)
        try:
            return node.activate_module(module_id, nodes)
            # return node.forward_rpc("gitar_connector", "gitar_activate_module", nodes)
        except Exception:
            traceback.print_exc(file=sys.stdout)
