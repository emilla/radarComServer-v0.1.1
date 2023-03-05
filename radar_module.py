import time
from register import Register
from communicator import SerialCom


class RadarModule:
    def __init__(self, com_config):
        self.com_config = com_config
        self.com = SerialCom(port=self.com_config['port'], rtscts=self.com_config['rtscts'])

        # create properties for each register

        self.mode_selection = {
            'address': 0x2,
            'rw': (True, True)
        }
        self.main_control = {
            'address': 0x3,
            'rw': (True, True)
        }
        self.status = {
            'address': 0x6,
            'rw': (True, False)
        }
        self.product_identification = {
            'address': 0x10,
            'rw': (True, False)
        }
        self.product_version = {
            'address': 0x11,
            'rw': (True, False)
        }
        self.streaming_control = {
            'address': 0x05,
            'rw': (True, True)
        }

        self.register_map = {
            'mode_selection': {
                'address': 0x2,
                'rw': (True, True)
            },
            'main_control': {
                'address': 0x3,
                'rw': (True, True)
            },
            'status': {
                'address': 0x6,
                'rw': (True, False)
            },
            'product_identification': {
                'address': 0x10,
                'rw': (True, False)},
            'product_version': {
                'address': 0x11,
                'rw': (True, False)},
            'streaming_control': {
                'address': 0x05,
                'rw': (True, True)}
        }

        # get module information

    async def get_module_info(self):
        await self.streaming_control.set_value(0x1)
        identification = await self.product_identification.get_value()
        version = await self.product_version.get_value()
        return identification, version

    # get module status
    async def get_module_status(self):
        await self.streaming_control.set_value(0x1)
        return await self.status.get_value()

    @staticmethod
    async def _configure_detector(self) -> None:
        await self.mode_selection.set_value(0x400)
        await self.range_start.set_value(500)
        await self.range_length.set_value(5000)
        await self.update_rate.set_value(1000)

    @staticmethod
    async def _initialize_module(self):
        await self.stop_module()
        print("Module stopped")

        await self._configure_detector(self)

        # create & activate module
        await self.main_control.set_value(3)

        # confirm module to be activated
        return await Register.value_matches(self.status, 2)

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
