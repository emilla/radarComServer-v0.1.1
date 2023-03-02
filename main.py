from display import Display
from presence_detector import PresenceDetector
import asyncio

display = Display(128, 64, 0x3C)


async def main():
    com_config = {
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'rtscts': True,
        'timeout': 2
    }
    mod_config = {
        'range_start': 300,
        'range_length': 5000
    }

    detector = PresenceDetector(mod_config, com_config)
    await detector.start_detector()


# Press the green button in the gutter to run the script.

if __name__ == '__main__':
    asyncio.run(main())
