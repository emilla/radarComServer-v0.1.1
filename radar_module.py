import time
from register_map import Register
from serial_com import SerialCom
import asyncio


class XMModule:
    def __init__(self, mod_config, com_config):
        self.mod_config = mod_config
        self.com_config = com_config
        self.com = SerialCom(port=self.com_config['port'], rtscts=self.com_config['rtscts'])

        # create properties for each register
        self.mode_selection = Register(address=0x2, rw=(True, True), com=self.com)
        self.main_control = Register(address=0x3, rw=(True, True), com=self.com)
        self.status = Register(address=0x6, rw=(True, False), com=self.com)
        self.product_identification = Register(address=0x10, rw=(True, False), com=self.com)
        self.product_version = Register(address=0x11, rw=(True, False), com=self.com)
        self.streaming_control = Register(address=0x05, rw=(True, True), com=self.com)

        # enable UART streaming
        self.streaming_control.value = 0x1

    # get module information
    def get_module_info(self):
        return self.product_identification.value, self.product_version.value

    @staticmethod
    async def _value_matches(self, register, value):
        # check if value matches
        duration = time.monotonic()
        while time.monotonic() - duration < 2:
            if register.value == value:
                return True
            await asyncio.sleep(0.1)
        return False

    # get module status
    def get_module_status(self):
        return self.status.value

    async def stop_module(self):
        # stop module
        self.main_control.value = 0
        await asyncio.sleep(0.3)

        # clear bits
        self.main_control.value = 4

        # confirm module to be ready
        async with self._value_matches(self, self.status, 0):
            pass

    # activate module
    async def initialize_module(self):
        await self.stop_module()
        print('Module stopped')
        # create & activate module
        self.main_control.value = 0x3
        print('Module created')
        await asyncio.sleep(0.3)

    @staticmethod
    def _decode_streaming_buffer(stream):
        assert stream[0] == 0xFD

        offset = 3

        result_info = {}

        while stream[offset] != 0xFE:
            address = stream[offset]
            offset += 1
            value = int.from_bytes(stream[offset:offset + 4], byteorder='little')
            offset += 4
            result_info[address] = value

        buffer = stream[offset + 3:]
        return result_info, buffer
