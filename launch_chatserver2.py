#launch_chatserver2.py
from chatserver3 import ChatServer

chatserver = ChatServer(port=20113, host='0.0.0.0')
chatserver.run()