from display.display import Display
from presence_detector import PresenceDetector
import asyncio

display = Display(128, 64, 0x3C)


def detector_data_handler(**kwargs):
    print(f'Presence: {"Person" if kwargs["presence"] else "Empty"} score={kwargs["score"]} '
          f'distance={kwargs["distance"]} m')

    if kwargs['presence']:
        display.draw_text('PERSON')
    else:
        display.draw_text('NOBODY')
    display.clear_display()


async def main():
    detector = PresenceDetector({
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'rtscts': True,
        'timeout': 2
    })
    await detector.start_presence_detector(
        duration=60,
        data_handler_func=detector_data_handler(),
        mod_config={
            'streaming_control': 0x1,
            'mode_selection': 0x400,
            'range_start': 500,
            'range_length': 5000,
            'update_rate': 1000,
        })


if __name__ == '__main__':
    asyncio.run(main())
