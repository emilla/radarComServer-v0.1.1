from serial_com import SerialCom
import asyncio


class Register:
    """
    Class for a register in the register map.
    """

    def __init__(self, address: int, rw: tuple, com: SerialCom) -> None:
        self.address = address
        self.write = rw[1]
        self.read = rw[0]
        self.com = com

    @property
    def value(self) -> int:
        if self.read:
            return self.com.register_read(self.address)
        else:
            raise ValueError('Register is not readable')

    @value.setter
    def value(self, value: int):
        if self.write:
            if value < 0 or value > 4294967295:
                raise ValueError('Invalid value for register')
            else:
                self.com.register_write(self.address, value)
        else:
            raise ValueError('Register is not writable')
