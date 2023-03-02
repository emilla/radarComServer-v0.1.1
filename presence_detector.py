import radar_module
import time
import asyncio
from register_map import Register
import struct


# detector class extends xm_module
class PresenceDetector(radar_module.XMModule):
    def __init__(self, mod_config, com_config):
        super().__init__(mod_config, com_config)

        if not mod_config['range_start']:
            mod_config['range_start'] = 5

        if not mod_config['range_length']:
            mod_config['range_length'] = 4

        # create properties for each register
        self.range_start = Register(address=0x20, rw=(True, True), com=self.com)
        self.range_length = Register(address=0x21, rw=(True, True), com=self.com)
        self.update_rate = Register(address=0x23, rw=(True, True), com=self.com)

        # enable UART streaming
        self.streaming_control.value = 0x1
        # set mode to presence
        self.mode_selection.value = 0x200
        # set range
        # self.range_start.value = mod_config['range_start'] * 1000
        # self.range_length.value = mod_config['range_length'] * 1000
        self.update_rate.value = 1

        # detection status
        self.detection_status = False

    def start_detector(self, duration=60, func=None):
        await self.initialize_module()
        start = time.monotonic()
        while time.monotonic() - start < duration:
            stream = self.com.read_stream()
            _result_info, buffer = self._decode_streaming_buffer(stream)

            (presence, score, distance) = struct.unpack("<bff", buffer)
            self.detection_status = presence
            print(f'Presence: {"True" if presence else "False"} score={score} distance={distance} m')
            if func:
                func(presence, score, distance)
