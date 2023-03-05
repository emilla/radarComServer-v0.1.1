from radar_module import RadarModule
import time
from register import Register
import struct


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
        # self.range_start = Register(address=0x20, rw=(True, True), com=self.com)
        # self.range_length = Register(address=0x21, rw=(True, True), com=self.com)
        # self.update_rate = Register(address=0x23, rw=(True, True), com=self.com)

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

    async def start_detector(self, duration=60, func=None, config=None):

        # Initialize module with config function
        print("Starting detector")
        await self._initialize_module(self, config)

        print(f"range_start: {await self.range_start.get_value()}")
        print(f"range_length: {await self.range_length.get_value()}")

        start = time.monotonic()
        while time.monotonic() - start < duration:
            stream = self.com.read_stream()
            _result_info, buffer = self._decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)

            print(f'Presence: {"True" if presence else "False"} score={score} distance={distance} m')
            if func:
                func(presence)

    async def stop_module(self):
        # stop module
        await self.main_control.set_value(0)

        # clear bits
        await self.main_control.set_value(4)

        # confirm module to be ready
        return
