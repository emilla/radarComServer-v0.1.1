import time
from register_map import Register
from serial_com import SerialCom
import asyncio


class XMModule:
    def __init__(self, com_config):
        self.com_config = com_config
        self.com = SerialCom(port=self.com_config['port'], rtscts=self.com_config['rtscts'])

        # create properties for each register
        self.mode_selection = Register(address=0x2, rw=(True, True), com=self.com)
        self.main_control = Register(address=0x3, rw=(True, True), com=self.com)
        self.status = Register(address=0x6, rw=(True, False), com=self.com)
        self.product_identification = Register(address=0x10, rw=(True, False), com=self.com)
        self.product_version = Register(address=0x11, rw=(True, False), com=self.com)
        self.streaming_control = Register(address=0x05, rw=(True, True), com=self.com)

    # get module information
    async def get_module_info(self):
        await self.streaming_control.set_value(0x1)
        return await self.product_identification.get_value(), await self.product_version.get_value()

    # get module status
    async def get_module_status(self):
        await self.streaming_control.set_value(0x1)
        return await self.status.get_value()

    @staticmethod
    async def _configure_detector(register_value_list) -> None:
        for register, value in register_value_list:
            await register.set_value(value)

    @staticmethod
    async def _value_matches(register, wanted_value):
        # check if value matches
        duration = time.monotonic()
        while time.monotonic() - duration < 2:
            if await register.get_value() == wanted_value:
                return True
            await asyncio.sleep(0.1)
        return False

    @staticmethod
    async def _initialize_module(self, mod_config):
        await self.stop_module()
        print("Module stopped")

        self._configure_detector(mod_config)

        # create & activate module
        await self.main_control.set_value(2)

        # confirm module to be activated
        return await self._value_matches(self.status, 2)

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
