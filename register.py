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
        Create a register from a dictionary, the dictionary should contain the "address", the "rw" read/write
        permissions, a SerialCom object to communicate with the module and an optional "options" dictionary.
        :param register_dict: dictionary with the register information
        :param com: SerialCom object to communicate with the module
        :param options:  dictionary with options for the register
        :return: Register object
        """
        if 'options' in register_dict:
            options = register_dict['options']
        else:
            options = None
        return cls(address=register_dict['address'], rw=register_dict['rw'], com=com, options=options)

    @classmethod
    async def definition_matches_value(cls, register, wanted_definition) -> bool:
        """
        Check if the value of the register matches the wanted definition
        :param register:  Register object
        :param wanted_definition:  string definition to check the register against
        :return:  True if the definition matches, False if not
        """
        cur_value = await register.get_value()
        duration = time.monotonic()
        while time.monotonic() - duration < 2:
            if cur_value == register.definitions[wanted_definition]:
                return True
            await asyncio.sleep(0.1)
        return False

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

    def __init__(self, address: int, rw: tuple, com: SerialCom, options=None) -> None:
        self.address = address
        self.write = rw[1]
        self.read = rw[0]
        self.com = com
        self.options = options
        # reverse the options dictionary to get a dictionary with the values as keys and the keys as values
        if self.options:
            self.definitions = {v: k for k, v in self.options.items()}
        else:
            self.definitions = None
        print(f"options: {self.options}")
        print(f"definitions: {self.definitions}")

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
            return

    async def get_definition(self):
        """
        Get the definition of the register
        :return: string with the definition of the register
        """
        if self.read and self.options:
            value = await self.get_value()
            print(f"get_definition value: {value}")
            if value in self.options:
                return self.options[value]
            else:
                return f'This value: {value} is not defined'
        else:
            raise ValueError('Register is not readable in get_definition')

    async def set_value(self, value: int):
        """
        Set the value of the register
        :param value: int value to set the register to
        :return: None
        """
        if self.options:
            if value not in self.options:
                raise ValueError('Invalid value for register')
        if self.write:
            if value < 0 or value > 4294967295:
                raise ValueError('Invalid value for register')
            else:
                self.com.register_write(self.address, value)
                await Register.value_matches(self, value)
        else:
            raise ValueError('Register is not writable')

    async def set_by_definition(self, definition: str):
        """
        Set the value of the register by the option name
        :param definition: string with the option name
        :return: None
        """
        if self.options is None:
            raise ValueError('This register does not have options')
        if definition in self.definitions:
            await self.set_value(self.definitions[definition])
        else:
            raise ValueError('Invalid option')
