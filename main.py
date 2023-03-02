from display import Display
from presence_detector import PresenceDetector

display = Display(128, 64, 0x3C)


def main():
    com_config = {
        'port': '/dev/ttyUSB0',
        'baudrate': 115200,
        'rtscts': True,
        'timeout': 2
    }
    mod_config = {
        'range_start': 5,
        'range_length': 4
    }
    detector = PresenceDetector(mod_config, com_config)
    print(detector.get_module_info())
    # detector.start_detector()


# Press the green button in the gutter to run the script.

if __name__ == '__main__':
    main()
