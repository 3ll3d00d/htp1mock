import asyncio
import websockets
import json

CHANNELS = ['lf', 'rf', 'c', 'sub1', 'sub2', 'sub3', 'ls', 'rs']


class Htp1:

    def __init__(self):
        self.__bands = {
            'peq': {
                'slots': [
                    {
                        'checksum': None,
                        'channels': {c: self.__make_peq() for c in CHANNELS}
                    } for i in range(16)
                ]
            }
        }
        self.__conns = set()

    @staticmethod
    def __make_peq(fc=120, gain=0, q=1):
        return {
            'Fc': fc,
            'gaindB': gain,
            'Q': q
        }

    async def on_msg(self, websocket, path):
        while True:
            try:
                data = await websocket.recv()
            except websockets.ConnectionClosed:
                print(f"Closed")
                break

            print(f"< {data}")

            if data.startswith('changemso'):
                print(f"Handling {data}")
                for operation in json.loads(data[9:]):
                    handled = False
                    if operation['op'] == 'replace':
                        tokens = [t for t in operation['path'].split('/') if t]
                        if len(tokens) == 6:
                            slots = self.__bands['peq']['slots']
                            slot_idx = int(tokens[2])
                            if len(slots) > slot_idx:
                                slot = slots[slot_idx]['channels']
                                if tokens[4] in slot:
                                    channel_filter = slot[tokens[4]]
                                    if tokens[5] in channel_filter:
                                        channel_filter[tokens[5]] = operation['value']
                                        print(f"Updated slot {tokens[4]} channel {tokens[5]} to {channel_filter}")

                    if not handled:
                        print(f"Unable to handle {operation}")
            elif data == 'getmso':
                pass # nop
            else:
                print(f"Ignoring {path} {data}")
            await websocket.send(json.dumps(self.__bands))


def main():
    htp1 = Htp1()
    start_server = websockets.serve(htp1.on_msg, "localhost", 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
