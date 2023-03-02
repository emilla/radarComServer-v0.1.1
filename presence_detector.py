import radar_module
import time
import asyncio
from register_map import Register
import struct


# detector class extends xm_module
class PresenceDetector(radar_module.XMModule):
    def __init__(self, mod_config, com_config):
        super().__init__(mod_config, com_config)

        # create properties for each register
        self.range_start = Register(address=0x20, rw=(True, True), com=self.com)
        self.range_length = Register(address=0x21, rw=(True, True), com=self.com)
        self.update_rate = Register(address=0x23, rw=(True, True), com=self.com)

        # enable UART streaming
        self.streaming_control.value = 0x1
        # set mode to presence
        self.mode_selection.value = 0x400

        # detection status
        self.detection_status = False

    async def configure_detector(self):
        await self._value_matches(self, self.mode_selection, 0x400)
        print(f"Mode set to presence: {self.mode_selection.value}")
        self.range_start.value = 250
        await self._value_matches(self, self.range_start, 200)
        self.range_length.value = 2000
        await self._value_matches(self, self.range_length, 2000)
        self.update_rate.value = 1000
        await asyncio.sleep(0.3)

    async def start_detector(self, duration=60, func=None):

        print("Starting detector")
        await self.initialize_module(self.configure_detector)
        print(f"range_start: {self.range_start.value}")
        print(f"range_length: {self.range_length.value}")

        start = time.monotonic()
        while time.monotonic() - start < duration:
            stream = self.com.read_stream()
            _result_info, buffer = self._decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)

            print(f'Presence: {"True" if presence else "False"} score={score} distance={distance} m')
            if func:
                func(presence, score, distance)
