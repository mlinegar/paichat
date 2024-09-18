import asyncio
import json
import os
import uuid
from datetime import datetime
from aiohttp import web
from handlers import handle, assets
from chat_logic import WebSocketExecutor
from config import external_port, host, initial_message

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

class ChatServer:
    def __init__(self, port=external_port, host=host):
        self.port = port
        self.host = host
        self.executors = []

    async def handle_websocket_chat(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        print("WebSocket connection opened")

        username = str(uuid.uuid4())  # Generate a unique username for this session

        chat_executor = WebSocketExecutor(ws)
        self.executors.append(chat_executor)

        await chat_executor.send_message(initial_message)

        try:
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
        finally:
            self.executors.remove(chat_executor)
            print("WebSocket connection closed")
        return ws
    
    async def handle_submit_problem(self, request):
        print("Received submit_problem request")
        data = await request.json()
        description = data.get('description', '')
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"problem_report_{timestamp}.txt"
        filepath = os.path.join(PROJECT_DIR, 'reports', filename)
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as file:
                file.write(description)
            print(f"Problem report saved: {filepath}")
            return web.Response(text='Problem report submitted successfully', status=200)
        except Exception as e:
            print(f"Error saving problem report: {e}")
            return web.Response(text='Error saving problem report', status=500)

    async def main(self):
        app = web.Application()
        app.add_routes([web.get('/', handle)])
        app.add_routes([web.get('/chat', self.handle_websocket_chat)])
        app.add_routes([web.post('/submit-problem', self.handle_submit_problem)])  # This line is correct for POST
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