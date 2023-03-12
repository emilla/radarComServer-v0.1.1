import asyncio

# Server data
address = "atom-radpi-01.local"
PORT = 7890
print("Server listening on Port " + str(PORT))

# A set of connected ws clients
connected = set()


async def serve_distance(websocket, path):
    print("A client just connected")
    # Store a copy of the connected client
    connected.add(websocket)
    # Handle incoming messages
    try:
        async for request in websocket:
            # convert request in JSON to python dictionary
            request = json.loads(request)

            # check if message is a request for distance
            if request["request"] == "distance":

                response = json.dumps({"result": distance_sensor.get_distance()})
            else:
                response = json.dumps({"error": "Message not understood"})
            for conn in connected:
                await conn.send(response)
    # Handle disconnecting clients
    except websockets.exceptions.ConnectionClosed as e:
        print("A client just disconnected")
    finally:
        connected.remove(websocket)


# Start the server
start_server = websockets.serve(serve_distance, address, PORT)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
