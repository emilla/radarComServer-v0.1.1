from communicator import SerialCom
import asyncio
import time


class Register:
    """
    Class for a register in the register map.
    """

    @classmethod
    def from_dict(cls, register_dict: dict, com: SerialCom) -> 'Register':
        """
        Create a register from a dictionary, the dictionary should contain the "address" and the "rw" read/write
        permissions
        :param register_dict: dictionary with the register information
        :param com: SerialCom object to communicate with the module
        :return: Register object
        """
        return cls(address=register_dict['address'], rw=register_dict['rw'], com=com)

    @classmethod
    def from_map_make_registers(cls, module, register_map: dict, com: SerialCom) -> None:
        """
        Create a register property for each register in the register map
        :param register_map: dictionary with the register information
        :param com: SerialCom object to communicate with the module
        :return: Register object
        :module: module to add the properties to
        """
        for key, value in register_map.items():
            module.setattr(cls, key, cls.from_dict(value, com))

    @classmethod
    async def value_matches(cls, register, wanted_value) -> bool:
        """
        Check if the value of the register matches the wanted value
        :param register:  Register object
        :param wanted_value:  int value to check the register against
        :return:  True if the value matches, False if not
        """
        cur_value = await register.get_value()
        duration = time.monotonic()
        while time.monotonic() - duration < 2:
            if cur_value == wanted_value:
                return True
            await asyncio.sleep(0.1)
        return False

    def __init__(self, address: int, rw: tuple, com: SerialCom) -> None:
        self.address = address
        self.write = rw[1]
        self.read = rw[0]
        self.com = com

    async def get_value(self):
        """
        Get the value of the register
        :return: a byte array with the value of the register
        """
        if self.read:
            value = self.com.register_read(self.address)
            # check if there is a value every 0.1 seconds for 2 seconds
            duration = time.monotonic()
            while time.monotonic() - duration < 2:
                if value:
                    return value
                await asyncio.sleep(0.1)

        else:
            raise ValueError('Register is not readable')

    async def set_value(self, value: int):
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
                await Register.value_matches(self, value)
        else:
            raise ValueError('Register is not writable')
