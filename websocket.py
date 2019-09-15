import main
import simulate
import json
import asyncio
import websockets
from dotenv import load_dotenv
load_dotenv()


async def connect():
    uri = "ws://connect.websocket.in/consumo?room_id=" + 1234
    async with websockets.connect(uri) as websocket:
        while True:
            print('waiting for messages...')
            request = await websocket.recv()
            requestJson = json.loads(request)
            if 'command' in requestJson:
                # TODO fix bug; simulate.main() causing exception in asyncio
                if(requestJson['command'] == 'start' and requestJson['type'] == 'simulate'):
                    print('starting simulation')
                    simulate.main()

                if(requestJson['command'] == 'start' and requestJson['type'] == 'main'):
                    print('starting main')
                    main.main()

            else:
                print(requestJson)


loop = asyncio.get_event_loop()
try:
    loop.create_task(connect())
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    print("Closing Loop")
    loop.stop()
    loop.close()
