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


def detector_data_handler(presence, score, distance):
    score = "{:.2f}".format(score)
    distance = "{:.1f}".format(distance)
    print(f'Presence: {"Person" if presence else "Empty"} || score={score} || distance={distance} meters')
    # convert score to string
    score = str(score)
    if presence:
        display.draw_text(score)
    else:
        display.draw_text('Vacant')
    display.clear_display()


async def main():
    global detector
    global display
    global address
    global PORT

    # Initialize detector
    async def message_router(websocket, path):
        global consumers, producer
        # check if the client is a producer or consumer
        try:
            if path == '/consumer':
                global consumers
                consumers.add(websocket)
                message = json.loads(websocket.recv())
                if message.keys()[0] == 'req':
                    await consumer_request_handler(message['data'], websocket)
                elif message.keys()[0] == 'cmd':
                    switcher = {
                        'start_detection': start_detection_cmd,
                        'stop_detection': stop_detection_cmd,
                        'connect_to_radar_module': connect_to_radar_module
                    }
                    # Get the function from switcher dictionary and call it passing the data dictionary as argument
                    await switcher[message['data']['type']](message['data'])

            elif path == '/producer':
                global producer
                if producer is None:
                    producer = websocket
                    message = json.loads(websocket.recv())
                    if message.keys()[0] == 'resp':
                        await producer_response_handler(message['data'], websocket)
                    elif message.keys()[0] == 'stream':
                        await broadcast_stream(message['data'], websocket)

            # Handle disconnecting clients
        except websockets.exceptions.ConnectionClosed as e:
            print("A client just disconnected")

        finally:
            consumers.remove(websocket)

    async def consumer_request_handler(websocket, data):
        """
        Handle requests from consumer clients, calls appropriate functions based on request type.
        :param websocket:
        :param data:
        :return: None
        """
        if data['type'] == 'status':
            await get_status(websocket)
        else:
            raise Exception('Invalid request type')

    async def producer_response_handler(message):
        """
        Handle responses from producer clients, this is not for streaming data, this is for responses to requests, for
        example,a status request.
        :param message:
        :return:
        """
        for consumer in consumers:
            await consumer.send(message)

    def connect_to_radar_module(com_config):
        """
        Create an instance of the PresenceDetector class and store it in the global variable detector.
        :param com_config:
        :return:
        """
        global detector
        detector = PresenceDetector(com_config)

    async def start_detection_cmd(mod_config):
        pass

    def stop_detection_cmd():
        pass

    async def get_status(websocket):
        global detector
        if detector is None:
            status = 'Not connected'
        else:
            status = await detector.get_module_status()
        await websocket.send(json.dumps({'resp': 'status',
                                         'data':
                                             {'module_status': status}
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

    start_server = websockets.serve(message_router, address, PORT)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    asyncio.run(main())
