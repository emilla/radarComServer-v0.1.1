import time
import serial


class ModuleError(Exception):
    """
    One of the error bits was set in the module
    """


class SerialCom:
    """
    Simple class to communicate with the module software
    """

    @classmethod
    def decode_streaming_buffer(cls, stream):
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

    def __init__(self, port, rtscts):
        self._port = serial.Serial(port, 115200, rtscts=rtscts,
                                   exclusive=True, timeout=2)

    def read_packet_type(self, packet_type):
        """
        Read any packet of packet_type. Any packages received with
        another type is discarded.
        """
        while True:
            header, payload = self._read_packet()
            if header[3] == packet_type:
                break
        return header, payload

    def _read_packet(self):
        header = self._port.read(4)
        length = int.from_bytes(header[1:3], byteorder='little')

        data = self._port.read(length + 1)
        assert data[-1] == 0xCD
        payload = data[:-1]
        return header, payload

    def register_write(self, addr, value):
        """
        Write a register
        """
        data = bytearray()
        data.extend(b'\xcc\x05\x00\xf9')
        data.append(addr)
        data.extend(value.to_bytes(4, byteorder='little', signed=False))
        data.append(0xcd)
        self._port.write(data)
        _header, payload = self.read_packet_type(0xF5)
        assert payload[0] == addr

    def register_read(self, addr):
        """
        Read a register
        """
        data = bytearray()
        data.extend(b'\xcc\x01\x00\xf8')
        data.append(addr)
        data.append(0xcd)
        self._port.write(data)
        _header, payload = self.read_packet_type(0xF6)
        assert payload[0] == addr
        return int.from_bytes(payload[1:5], byteorder='little', signed=False)

    def buffer_read(self, offset):
        """
        Read the buffer
        """
        data = bytearray()
        data.extend(b'\xcc\x03\x00\xfa\xe8')
        data.extend(offset.to_bytes(2, byteorder='little', signed=False))
        data.append(0xcd)
        self._port.write(data)

        _header, payload = self.read_packet_type(0xF7)
        assert payload[0] == 0xE8
        return payload[1:]

    def read_stream(self):
        """
        Read a stream of data
        """
        _header, payload = self.read_packet_type(0xFE)
        return payload

    @staticmethod
    def _check_error(status):
        ERROR_MASK = 0xFFFF0000
        if status & ERROR_MASK != 0:
            ModuleError(f"Error in module, status: 0x{status:08X}")

    @staticmethod
    def _check_timeout(start, max_time):
        if (time.monotonic() - start) > max_time:
            raise TimeoutError()

    def _wait_status_set(self, wanted_bits, max_time):
        """
        Wait for wanted_bits bits to be set in status register
        """
        start = time.monotonic()

        while True:
            status = self.register_read(0x6)
            self._check_timeout(start, max_time)
            self._check_error(status)

            if status & wanted_bits == wanted_bits:
                return
            time.sleep(0.1)

    def wait_start(self):
        """
        Poll status register until created and activated
        """
        ACTIVATED_AND_CREATED = 0x3
        self._wait_status_set(ACTIVATED_AND_CREATED, 3)

    def wait_for_data(self, max_time):
        """
        Poll status register until data is ready
        """
        DATA_READY = 0x00000100
        self._wait_status_set(DATA_READY, max_time)
