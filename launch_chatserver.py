import lmql
import sys
import os
file = "chat.lmql"
# works
from lmql.lib.chat import chatserver
chatserver(file, port=18089, host='0.0.0.0').run()

# from chat.output import ChatMessageOutputWriter, MessageDecorator

# message = MessageDecorator()

# from chat.chatserver import ChatServer

# def chatserver(*args, **kwargs):
#     """
#     Constructs a chatserver instance with the given arguments.
#     """
#     return ChatServer(*args, **kwargs)

# if __name__ == "__main__":
#     server = chatserver(file, port=18089, host='0.0.0.0')
#     server.run()