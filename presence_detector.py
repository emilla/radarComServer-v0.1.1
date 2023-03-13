from radar_module import RadarModule
import time
import struct
from communicator import SerialCom
import websockets


# detector class extends xm_module
class PresenceDetector(RadarModule):
    """
    Class for the presence detector module. Inherits from the RadarModule class
    """

    def __init__(self, com_config):
        """
        Initialize the presence detector module
        :param com_config:  dictionary with the configuration for the serial communication. Should contain the port and
        rtscts settings (True or False)
        """
        self.streaming = False
        super().__init__(com_config)
        # validate the configuration
        # create properties for each register
        self.presence_register_map = {
            'range_start': {
                'address': 0x20,
                'rw': (True, True)
            },
            'range_length': {
                'address': 0x21,
                'rw': (True, True)
            },
            'update_rate': {
                'address': 0x23,
                'rw': (True, True)
            },
            'profile_selection': {
                'address': 0x28,
                'rw': (True, True),
                'options': {
                    1: 'profile_1',
                    2: 'profile_2',
                    3: 'profile_3',
                    4: 'profile_4',
                    5: 'profile_5',
                }
            },
            'sensor_power_mode': {
                'address': 0x25,
                'rw': (True, True),
                'options': {
                    0: 'off',
                    1: 'sleep',
                    2: 'ready',
                    3: 'active',
                    4: 'hibernate'
                }
            }
        }

        # validate the communication configuration
        super()._validate_com_config(com_config)

        # create properties for each register in the presence register map
        super()._make_registers(self, self.presence_register_map)

        # detector configuration
        self.default_mod_config = {
            'streaming_control': 0x1,
            'mode_selection': 0x400,
            'range_start': 500,
            'range_length': 5000,
            'update_rate': 1000,
            'profile_selection': 5,
            'sensor_power_mode': 3
        }
        # set default configuration

    async def start_stream(self, data_handler_func=None, duration=60):
        print("Starting detector")
        start = time.monotonic()

        while time.monotonic() - start < duration:

            stream = self.com.read_stream()
            _result_info, buffer = SerialCom.decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)

            if data_handler_func:
                await data_handler_func(presence=presence, score=score, distance=distance)

    @staticmethod
    def _validate_mod_config(mod_config):
        """
        checks that config dictionary contains all required keys
        :param mod_config:  dictionary with the configuration parameters. Requires keys: range_start, range_length, update_
        rate,
        :return:
        """
        for key in ['range_start', 'range_length', 'update_rate', 'streaming_control', 'mode_selection']:
            # if key is not in config dictionary or value is not an integer raise error
            if key not in mod_config:
                raise ValueError(f'Missing register {key}, or value is not an integer')
        return True
