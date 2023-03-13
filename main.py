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


async def message_router(websocket, path):
    global consumers
    while True:
        try:
            global consumers
            if websocket not in consumers:
                print("A new client has just connected")
                consumers.add(websocket)
            payload = await websocket.recv()

            message = json.loads(payload)
            if next(iter(message.keys())) == 'req':
                switcher = {
                    'status': get_status_req,
                }
                # Get the function from switcher dictionary and call it passing the data dictionary as argument
                await switcher[message['req']](websocket, message['data'])
            elif next(iter(message.keys())) == 'cmd':
                switcher = {
                    'start_detector': start_detector_cmd,
                    'stop_detector': stop_detector_cmd,
                    'open_serial': open_serial_cmd
                }
                # Get the function from switcher dictionary and call it passing the data dictionary as argument
                await switcher[message['cmd']](websocket, message['data'])
            # Handle disconnecting clients
        except websockets.exceptions.ConnectionClosed as e:
            print("A client just disconnected")

    # finally:
    #     consumers.remove(websocket)


async def open_serial_cmd(websocket, data):
    com_config = {
        'port': data['port'],
        'baudrate': int(data['baudrate']),
        'rtscts': bool(data['rtscts']),
        'timeout': int(data['timeout'])
    }

    global detector
    detector = PresenceDetector(com_config)
    print("detector instantiated & communicator configured with port:" + data['port'])
    await asyncio.sleep(0.1)
    await websocket.send(json.dumps({'ack': 'success', 'data': {'comment': 'Serial port opened'}}))


async def start_detector_cmd(websocket, data):
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
        if await detector.create_module(mod_config):
            print("module created")
            await asyncio.sleep(0.1)
            await websocket.send(
                json.dumps({'ack': 'success', 'data': {'comment': 'Module created, activating module'}}))
            # activate module
            if await detector.activate_module():
                print("module activated")
                await asyncio.sleep(0.1)
                await websocket.send(
                    json.dumps({'ack': 'success', 'data': {'comment': 'Module activated, starting module'}}))
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(asyncio.wait_for(detector.start_stream(detector_data_handler), timeout=30))
                    loop.run_forever()
                except asyncio.TimeoutError:
                    print("Error starting stream")
        else:
            status, status_def = await detector.get_module_status()
            raise Exception(
                f'Something went wrong, module not created & activated, detector status: {status} - {status_def}')


async def stop_detector_cmd(websocket, data=None):
    global detector
    if detector is not None:
        if await detector.stop_module():
            await websocket.send(json.dumps({'ack': 'success', 'data': {'comment': 'Module stopped'}}))
            detector = None
        else:
            raise Exception('Failed to stop detector')


async def get_status_req(websocket, data=None):
    global detector
    if detector is None:
        status = 'null'
        status_def = 'No serial connection opened'
    else:
        try:
            status, status_def = await detector.get_module_status()
        except Exception as e:
            status = 'null'
            status_def = f'Unknown error: {e}'

    await websocket.send(json.dumps({'resp': 'status',
                                     'data': {'status': status,
                                              'status_def': status_def
                                              }
                                     }))


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
