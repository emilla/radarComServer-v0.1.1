from display.display import Display
from presence_detector import PresenceDetector
import asyncio

display = Display(128, 64, 0x3C)


def detector_data_handler(presence, score, distance):
    score = "{:.2f}".format(score)
    distance = "{:.1f}".format(distance)
    print(f'Presence: {"Person" if presence else "Empty"} score={score}, distance={distance} meters')
    # convert score to string
    score = str(score)
    if presence:
        display.draw_text(score)
    else:
        display.draw_text('Vacant')
    display.clear_display()


async def main():
    detector = PresenceDetector({
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'rtscts': True,
        'timeout': 2
    })
    await detector.start_detection(
        duration=60,
        data_handler_func=detector_data_handler,
        mod_config={
            'streaming_control': 0x1,
            'mode_selection': 0x400,
            'range_start': 500,
            'range_length': 5000,
            'update_rate': 1000,
            'profile_selection': 5,
            'sensor_power_mode': 3
        })


if __name__ == '__main__':
    asyncio.run(main())
