from display.display import Display
from presence_detector import PresenceDetector
import asyncio

display = Display(128, 64, 0x3C)


def update_display(presence):
    if presence:
        display.draw_text('PERSON')
    else:
        display.draw_text('NOBODY')
    display.clear_display()


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

    await detector.start_detector(duration=60, func=update_display)


if __name__ == '__main__':
    asyncio.run(main())
