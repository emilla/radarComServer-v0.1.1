from radar_module import RadarModule
import time
import struct
from communicator import SerialCom


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
        }
        # set default configuration

    async def start_presence_detector(self, duration=60, data_handler_func=None, mod_config=None):
        """
        Start detector and print results
        :param duration: duration in seconds
        :param data_handler_func: function to be called with presence as argument
        :param mod_config: module configuration parameters. Requires keys: range_start, range_length, update_rate,
        streaming_control, mode_selection or provide None to use default configuration
        :return:
        """
        # Initialize module with config parameter, if none is given or if the config is not valid, use default config
        if mod_config is not None:
            if not self._validate_mod_config(mod_config):
                raise ValueError("Configuration provided is not valid, using default configuration")
        else:
            mod_config = self.default_mod_config

        await super()._initialize_module(self, mod_config)

        # Run module
        print("Starting detector")
        start = time.monotonic()
        while time.monotonic() - start < duration:

            stream = self.com.read_stream()
            _result_info, buffer = SerialCom.decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)
            print(f'Presence: {"True" if presence else "False"} score={score} distance={distance} m')
            if data_handler_func:
                data_handler_func(presence=presence, score=score, distance=distance)

    async def stop_detector(self, clean_up_func=None):
        """
        Stop detector
        :param clean_up_func: function to be called with is_stopped as argument (True if stopped, False if not)
        :return:
        """

        # Stop module and clean up serial communication
        is_stopped = await super()._stop_clear_module(self)

        # function to be called after stopping the module, if given.
        if clean_up_func:
            clean_up_func(is_stopped)
        return is_stopped

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
            if key not in mod_config or not isinstance(mod_config[key], int):
                raise ValueError(f'Missing register {key}, or value is not an integer')
        return True
