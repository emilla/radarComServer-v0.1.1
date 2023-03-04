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

        self._value = None

    async def get_value(self) -> int:
        """
        Get the value of the register
        :return: a byte array with the value of the register
        """
        if self.read:
            return await self.com.register_read(self.address)
        else:
            raise ValueError('Register is not readable')

    async def set_value(self, value: int) -> None:
        """
        Set the value of the register
        :param value: int value to set the register to
        :return: None
        """
        if self.write:
            if value < 0 or value > 4294967295:
                raise ValueError('Invalid value for register')
            else:
                self.com.register_write(self.address, value)
                while value != await self.get_value():
                    await asyncio.sleep(0.1)
        else:
            raise ValueError('Register is not writable')
