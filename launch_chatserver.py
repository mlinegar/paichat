# from lmql.lib.chat import chatserver
from chat import chatserver
chatserver('chat.lmql', port=18089, host='0.0.0.0').run()
