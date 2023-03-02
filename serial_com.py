import serial


class SerialCom:
    def __init__(self, port: str, rtscts: bool = True, timeout: int = 2) -> None:
        """
        Initializes the ModuleCommunication object.

        Args:
            port (str): The name of the serial port to use.
            rtscts (bool, optional): Whether to use RTS/CTS flow control. Defaults to True.
            timeout (int, optional): The timeout for serial communication. Defaults to 2 seconds.
        """
        self._port = serial.Serial(port, 115200, rtscts=rtscts, exclusive=True, timeout=timeout)

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

    def register_write(self, addr, value) -> None:
        """
        Writes a value to the given register address.

        Args:
            addr (int): The address of the register to write to.
            value (int): The value to write to the register.
        """
        data = bytes([0xcc, 0x05, 0x00, 0xf9, addr]) + value.to_bytes(4, byteorder='little', signed=False) + bytes(
            [0xcd])
        self._port.write(data)

        _header, payload = self.read_packet_type(0xF5)
        assert payload[0] == addr

    def register_read(self, addr: int) -> int:
        """
        Reads the value of the given register address.

        Args:
            addr (int): The address of the register to read from.

        Returns:
            The value of the register.
        """
        data = bytes([0xcc, 0x01, 0x00, 0xf8, addr, 0xcd])
        self._port.write(data)

        header, payload = self.read_packet_type(0xF6)
        assert payload[0] == addr, f"Expected addr {addr} but got {payload[0]}"
        assert len(payload) == 5, f"Expected payload length of 5 but got {len(payload)}"

        return int.from_bytes(payload[1:], byteorder='little', signed=False)

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
    def _check_error(status: int) -> None:
        """
        Checks if there is an error in the module status.

        Args:
            status (int): The module status to check.
        """
        ERROR_MASK = 0xFFFF0000
        assert status & ERROR_MASK == 0, f"Error in module, status: 0x{status:08}"
