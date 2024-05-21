import os
from aiohttp import web

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))

def handle(request):
    index = open(os.path.join(PROJECT_DIR, 'chat/assets/index.html')).read()
    return web.Response(text=index, content_type='text/html')

def assets(request):
    path = request.match_info.get('path', '')
    if not path.startswith('chat_assets/'):
        return web.Response(text='not found', status=404)
    path = path.replace('chat_assets/', PROJECT_DIR + '/chat/assets/')
    return web.FileResponse(path)
