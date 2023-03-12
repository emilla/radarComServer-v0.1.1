from display.display import Display
import websockets
from presence_detector import PresenceDetector
import asyncio
import json

# Global variables
detector = None
consumers = set()
producer = None
display = Display(128, 64, 0x3C)
address = "atom-radpi-01.local"
PORT = 7890


async def detector_data_handler(presence, score, distance):
    score = "{:.2f}".format(score)
    global display
    distance = "{:.1f}".format(distance)
    print(f'Presence: {"Person" if presence else "Empty"} || score={score} || distance={distance} meters')
    # convert score to string
    score = str(score)
    if presence:
        display.draw_text(score)
    else:
        display.draw_text('Vacant')
    display.clear_display()

    # Send data to all connected consumers
    message = {'stream': 'presence', 'data': {"presence": presence, "score": score, "distance": distance}}
    await broadcast_stream(message)


# Initialize detector
async def message_router(websocket, path):
    global consumers
    while True:
        try:
            print("A consumer just connected")

            global consumers
            consumers.add(websocket)
            payload = await websocket.recv()

            message = json.loads(payload)
            if next(iter(message.keys())) == 'req':
                await consumer_request_handler(websocket, message['data'])
            elif next(iter(message.keys())) == 'cmd':
                switcher = {
                    'start_detector': start_detector_cmd,
                    'stop_detector': stop_detector_cmd,
                    'open_serial': open_serial_cmd
                }
                # Get the function from switcher dictionary and call it passing the data dictionary as argument
                await switcher[message['cmd']](message['data'])
            # Handle disconnecting clients
        except websockets.exceptions.ConnectionClosed as e:
            print("A client just disconnected")

    # finally:
    #     consumers.remove(websocket)


async def consumer_request_handler(websocket, data):
    """
    Handle requests from consumer clients, calls appropriate functions based on request type.
    :param websocket:
    :param data:
    :return: None
    """
    if data['type'] == 'status':
        await get_status_req(websocket)
    else:
        raise Exception('Invalid request type')


async def open_serial_cmd(data):
    """
    Create an instance of the PresenceDetector class and store it in the global variable detector.
    :param data: A dictionary containing the configuration data for the radar module
    :return:
    """
    com_config = {
        'port': data['port'],
        'baudrate': int(data['baudrate']),
        'rtscts': bool(data['rtscts']),
        'timeout': int(data['timeout'])
    }

    global detector
    detector = PresenceDetector(com_config)
    await asyncio.sleep(0.1)


async def start_detector_cmd(data):
    """
    Start the presence detection process
    :param data: A dictionary containing the configuration data for the radar module
    :return:
    """
    mod_config = {
        'streaming_control': data['streaming_control'],
        'mode_selection': data['mode_selection'],
        'range_start': int(data['range_start']),
        'range_length': int(data['range_length']),
        'update_rate': int(data['update_rate']),
        'profile_selection': data['profile_selection'],
        'sensor_power_mode': 'active',
    }

    global detector
    if detector is not None:
        await detector.start_detector(detector_data_handler, mod_config, 30)
    else:
        raise Exception('No radar module connected')


async def stop_detector_cmd(message):
    global detector
    if detector is not None:
        if await detector.stop_detector():
            detector = None

        else:
            raise Exception('Failed to stop detector')


async def get_status_req(websocket):
    global detector
    if detector is None:
        status = 'Not connected'
    else:
        try:
            status = await detector.get_module_status_definition()
        except Exception as e:
            status = 'Unknown'

    await websocket.send(json.dumps({'resp': 'status',
                                     'data': {'module_status': status}}))


async def broadcast_stream(message):
    """
    Broadcast a message to all connected consumer clients. This is for streaming data, not for responses to requests
    :param message:
    :return:
    """
    global consumers
    for consumer in consumers:
        await consumer.send(json.dumps(message))


start_server = websockets.serve(message_router, address, PORT)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

# detector = PresenceDetector({
#     'port': '/dev/ttyUSB0',
#     'baudrate': 115200,
#     'rtscts': True,
#     'timeout': 2
# })
# await detector.start_detection(
#     duration=60,
#     data_handler_func=detector_data_handler,
#     mod_config={
#         'streaming_control': 0x1,
#         'mode_selection': 0x400,
#         'range_start': 500,
#         'range_length': 5000,
#         'update_rate': 1000,
#         'profile_selection': 5,
#         'sensor_power_mode': 3
#     })
