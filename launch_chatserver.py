from lmql.lib.chat import chatserver

chatserver('chat.lmql', port=18089, host='0.0.0.0').run()
# chatserver('chat.lmql', port=18089, host='localhost').run()
