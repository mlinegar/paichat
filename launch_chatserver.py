# from lmql.lib.chat import chatserver
from chat import chatserver
chatserver('chat.lmql', port=12345, host='0.0.0.0').run()