from display import Display
from presence_detector import PresenceDetector

display = Display(128, 64, 0x3C)


def main():
    config = {
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'rtscts': True,
        'timeout': 2
    }
    detector = PresenceDetector({}, config)
    detector.start_detector(lambda x: display.draw_text(str(x)))


# Press the green button in the gutter to run the script.

if __name__ == '__main__':
    main()
