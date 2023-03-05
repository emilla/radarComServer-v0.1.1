import time
from register import Register
from communicator import SerialCom


class RadarModule:
    def __init__(self, com_config):
        self.com = SerialCom(port=com_config['port'], rtscts=com_config['rtscts'])

        self.general_register_map = {
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
                'rw': (True, False)
            },
            'product_version': {
                'address': 0x11,
                'rw': (True, False)
            },
            'streaming_control': {
                'address': 0x05,
                'rw': (True, True)
            }
        }

        self._make_registers(self, self.general_register_map)

    async def get_module_info(self):
        await self.streaming_control.set_value(0x1)
        identification = await self.product_identification.get_value()
        version = await self.product_version.get_value()
        return identification, version

    # get module status
    async def get_module_status(self):
        await self.streaming_control.set_value(0x1)
        return await self.status.get_value()

    # create properties for each register
    @staticmethod
    def _make_registers(self, register_map):
        for key, value in register_map.items():
            setattr(self, key, Register.from_dict(value, self.com))

    @staticmethod
    async def _configure_detector(self, config) -> None:
        # iterate over config dict and set values
        for key, value in config.items():
            print(f"{key}: {value}")
            await getattr(self, key).set_value(value)

    @staticmethod
    async def _initialize_module(self, config=None):
        await self.stop_module()
        print("Module stopped")

        print("Configuring module")
        await self._configure_detector(self, config)

        # create & activate module
        print("Activating module")
        await self.main_control.set_value(3)

        # confirm module to be activated
        return await Register.value_matches(self.status, 2)

    #   TODO: move this to Register class
    @staticmethod
    def _decode_streaming_buffer(stream):
        """
        Decode streaming buffer
        :param stream: streaming buffer
        :return:  result_info, buffer (result_info is a dict with address as key and value as value)
        """
        # check if stream starts with 0xFD
        assert stream[0] == 0xFD

        # offset to start of result info
        offset = 3
        result_info = {}

        # read result info until 0xFE is reached
        while stream[offset] != 0xFE:
            address = stream[offset]
            offset += 1
            value = int.from_bytes(stream[offset:offset + 4], byteorder='little')
            offset += 4
            result_info[address] = value

        # read rest of buffer (contains data) and return it
        buffer = stream[offset + 3:]
        return result_info, buffer
