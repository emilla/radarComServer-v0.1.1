from serial_com import SerialCom


class Register:
    """
    Class for a register in the register map.
    """
    def __init__(self, address: int, rw: tuple, com: SerialCom) -> None:
        self.address = address
        self.value = None
        self.write = (rw[1] == 'w')
        self.read = (rw[0] == 'r')
        self.options = {}
        self.com = com

    @property
    def value(self) -> int:
        if self.read:
            return self.com.register_read(self.address)
        else:
            raise ValueError('Register is not readable')

    @value.setter
    def value(self, value: int) -> None:
        # check if value is in options
        if self.write:
            self.com.register_write(self.address, value)
        else:
            raise ValueError('Invalid value for register')
