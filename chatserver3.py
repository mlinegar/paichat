import asyncio
import json
from aiohttp import web
from handlers import handle, assets
from chat_logic import WebSocketExecutor
from config import external_port, host, initial_message

class ChatServer:
    def __init__(self, port=external_port, host=host):
        self.port = port
        self.host = host
        self.executors = []

    async def handle_websocket_chat(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        print("WebSocket connection opened")

        chat_executor = WebSocketExecutor(ws)
        self.executors.append(chat_executor)

        await chat_executor.send_message(initial_message)

        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                else:
                    data = json.loads(msg.data)
                    print(f"Received message: {data}")
                    if data["type"] == "input":
                        await chat_executor.handle_input(data["text"])
            elif msg.type == web.WSMsgType.ERROR:
                print(f'ws connection closed with exception {ws.exception()}')
        self.executors.remove(chat_executor)
        print("WebSocket connection closed")
        return ws

    async def main(self):
        app = web.Application()
        app.add_routes([web.get('/', handle)])
        app.add_routes([web.get('/chat', self.handle_websocket_chat)])
        app.add_routes([web.get('/{path:.*}', assets)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f'🤖 Your chatbot is waiting for you at http://{self.host}:{self.port}', flush=True)

        while True:
            await asyncio.sleep(3600)

    def run(self):
        asyncio.run(self.main())


if __name__ == '__main__':
    chatserver = ChatServer(port=external_port, host=host)
    chatserver.run()