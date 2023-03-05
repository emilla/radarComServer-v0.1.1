from radar_module import RadarModule
import time
import struct
from communicator import SerialCom


# detector class extends xm_module
class PresenceDetector(RadarModule):
    def __init__(self, com_config):
        super().__init__(com_config)

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

        self._make_registers(self, self.presence_register_map)

        # detector configuration
        self.default_mod_config = {
            'range_start': 500,
            'range_length': 5000,
            'update_rate': 1000,
            'streaming_control': 0x1,
            'mode_selection': 0x400,
        }
        # set default configuration

    async def start_detector(self, duration=60, handle_data_func=None, mod_config=None):
        """
        Start detector and print results
        :param duration: duration in seconds
        :param handle_data_func: function to be called with presence as argument
        :param mod_config: module configuration parameters. Requires keys: range_start, range_length, update_rate,
        streaming_control, mode_selection or provide None to use default configuration
        :return:
        """
        # Initialize module with config parameter, if none is given use default config
        if mod_config is None:
            mod_config = self.default_mod_config
        await self._initialize_module(self, mod_config)

        # print measuring info
        print(f"range_start: {await self.range_start.get_value()}")
        print(f"range_length: {await self.range_length.get_value()}")

        # Run module
        print("Starting detector")
        start = time.monotonic()
        while time.monotonic() - start < duration:

            stream = self.com.read_stream()
            _result_info, buffer = SerialCom.decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)

            print(f'Presence: {"True" if presence else "False"} score={score} distance={distance} m')
            if handle_data_func:
                handle_data_func(presence=presence, score=score, distance=distance)

    async def stop_detector(self, clean_up_func=None):
        """
        Stop detector
        :param clean_up_func: function to be called with is_stopped as argument (True if stopped, False if not)
        :return:
        """
        is_stopped = await self._stop_clear_module(self)
        if clean_up_func:
            clean_up_func(is_stopped)
        return is_stopped
