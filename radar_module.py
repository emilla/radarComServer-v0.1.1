import time
from register import Register
from communicator import SerialCom


class RadarModule:
    def __init__(self, com_config):
        self.com = SerialCom(port=com_config['port'], rtscts=com_config['rtscts'])

        self.general_register_map = {
            'mode_selection': {
                'address': 0x2,
                'rw': (True, True),
                'options': {
                    0x1: 'power_bins',
                    0x2: 'Envelope',
                    0x4: 'sparse',
                    0x200: 'distance',
                    0x400: 'presence'
                }
            },
            'main_control': {
                'address': 0x3,
                'rw': (False, True),
                'options': {
                    0: 'stop',
                    1: 'create',
                    2: 'activate',
                    3: 'create_activate',
                    4: 'clear_status',
                }
            },
            'status': {
                'address': 0x6,
                'rw': (True, False),
                'options': {
                    0: "No bits set",
                    0x000000FF: "Bits can't be cleared with clear_status",
                    0xFFFFFF00: "Mask with bits that can be cleared",
                    0xFFFF0000: "Mask with Error bits",
                    0x00000001: "Server or Detector Created",
                    0x00000002: "Server or Detector Activated",
                    0x00000100: "Data is ready to be read from the buffer",
                    0x00010000: "Error occurred in the module",
                    0x00020000: "Invalid command or parameter received",
                    0x00040000: "Invalid mode",
                    0x00080000: "Error creating the requested service or detector",
                    0x00100000: "Error activating the requested service or detector",
                    0x00200000: "An attempt to write a register or read the buffer when the module is in wrong state"
                }
            },
            'product_identification': {
                'address': 0x10,
                'rw': (True, False),
                'options': {
                    0xACC2: "XM132"
                }
            },
            'product_version': {
                'address': 0x11,
                'rw': (True, False)
            },
            'streaming_control': {
                'address': 0x05,
                'rw': (True, True),
                'options': {
                    0: 'streaming_disabled',
                    1: 'streaming_enabled'
                }
            }
        }

        self._make_registers(self, self.general_register_map)

    async def get_module_info(self):
        """
        Get module identification and version
        :return:  identification, version as tuple
        """
        await self.streaming_control.set_value(0x1)
        identification = await self.product_identification.get_value()
        version = await self.product_version.get_value()
        status = await self.status.get_value()
        return status, identification, version

    async def get_module_status(self):
        """
        Get module status
        :return:  status as int
        """
        await self.streaming_control.set_value(0x1)
        return await self.status.get_value()


    @staticmethod
    def _validate_com_config(com_config):
        """
        checks that port is set and value is valid, and that rtscts is set and value is valid
        :param com_config:  dictionary with the configuration for the serial communication. Should contain the port and
        rtscts settings (True or False)
        :return:
        """
        if 'port' not in com_config:
            raise ValueError("Port not set")
        if 'rtscts' not in com_config:
            raise ValueError("rtscts not set")
        # check that port is a string in format 'COMx' or '/dev/ttyUSBx'
        if not isinstance(com_config['port'], str):
            raise ValueError("Port must be a string")
        if not (com_config['port'].startswith('COM') or com_config['port'].startswith('/dev/ttyUSB')):
            raise ValueError("Port must be in format 'COMx' or '/dev/ttyUSBx'")
        if not isinstance(com_config['rtscts'], bool):
            raise ValueError("rtscts must be a bool")

    @staticmethod
    def _make_registers(self, register_map):
        """
        Create properties for each register in the register map
        :param self:  instance of the class
        :param register_map:  dictionary with the register map
        :return:  None
        """
        for key, value in register_map.items():
            setattr(self, key, Register.from_dict(value, self.com))
            print(f"Register {key} created")

    @staticmethod
    async def _configure_module(self, config) -> None:
        """
        Configure detector with config parameters in config dictionary
        :param self:  instance of the class
        :param config:  dictionary with the configuration parameters. Requires keys: range_start, range_length,
        update_rate,
        :return:  None
        """
        if config is None:
            return
        print("Configuring Module")
        for key, value in config.items():
            # get register from instance of the class by name (key)
            register = getattr(self, key)
            # set value of current register
            if isinstance(value, int):
                await register.set_value(value)
                print(f"-{key} set to: {await register.get_value()}")
            elif isinstance(value, str):
                await register.set_by_definition(value)
                print(f"-{key} set to: {await register.get_value_with_definition()}")

    @staticmethod
    async def _create_module(self, config=None):
        """
        Initialize module with config parameter if given
        :param self:  instance of the class
        :param config:  dictionary with the configuration parameters. Requires keys: range_start, range_length,
        :return:  bool: True if successful, False if not
        """
        try:
            await self._stop_clear_module(self)
            await self._configure_module(self, config)
            await self.main_control.set_value(1)
            if not await Register.value_matches(self.status, 1):
                print(f"Module not ready, status: {await self.status.get_value()}")
                return False
            return True
        except Exception as e:
            print(f"Error while creating module: {e}")
            return False

    @staticmethod
    async def _activate_module(self):
        print("Activating module")
        try:
            await self.main_control.set_value(2)
            status_def = await self.status.get_value_with_definition()
            status = await self.status.get_value()
            print(f'Sensor status: {status} : {status_def}')
            return await Register.value_matches(self.status, 2)
        except Exception as e:
            print(f"Error while activating module: {e}")
            return False

    @staticmethod
    async def _stop_clear_module(self):
        """
        Stop module and clear bits
        :return:
        """
        cmd_stop = 0
        await self.main_control.set_value(cmd_stop)

        cmd_clear_bits = 4
        await self.main_control.set_value(cmd_clear_bits)
        print("Module stopped and cleared")
        if await Register.value_matches(self.status, 0):
            return True
