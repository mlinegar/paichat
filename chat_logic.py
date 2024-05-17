import json
import os
import openai
import logging
import asyncio
import datetime
import uuid
from pathlib import Path
from tinydb import TinyDB, JSONStorage
from tinydb.middlewares import CachingMiddleware
from tenacity import retry, stop_after_attempt, wait_random_exponential
from config import system_prompt, script, error_message, large_model, small_model
from my_generate import my_generate

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setting up database and logger
user_id = str(uuid.uuid4())
path = Path(f"output/{user_id}.db")
db = TinyDB(path, storage=CachingMiddleware(JSONStorage))

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    handler = logging.FileHandler(log_file, mode='w')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

chat_logger = setup_logger('chat_logger', f'logging/{user_id}.log')

# Function to log messages
def log_messages(chat_logger, messages, level="info"):
    for label, value in messages.items():
        formatted_message = f"{label}: {value}"
        if level == "info":
            chat_logger.info(formatted_message)
        elif level == "error":
            chat_logger.error(formatted_message)

# Function to log data to the database
def log_to_database(db, data):
    db.insert(data)
    db.storage.flush()  # force save

class WebSocketExecutor:
    def __init__(self, ws):
        self.ws = ws
        self.chat_history = [{"role": "system", "content": system_prompt}]
        self.current_step = 0
        self.current_question = 0
        self.script = script
        self.message_id = 0
        self.errors = 0
        self.tries = 0

    async def send_message(self, message, complete=False):
        self.message_id += 1
        self.chat_history.append({"role": "assistant", "content": message})
        await self.ws.send_str(json.dumps({
            "type": "response",
            "data": message,
            "complete": complete,
            "message_id": self.message_id
        }))
        log_messages(chat_logger, {"Sent message": message})
        log_to_database(db, {
            "message_id": self.message_id,
            "role": "assistant",
            "content": message,
            "complete": complete
        })

    async def handle_input(self, user_input):
        print(f"Handling user input: {user_input}")
        self.chat_history.append({"role": "user", "content": user_input})
        log_messages(chat_logger, {"User input": user_input})
        log_to_database(db, {
            "message_id": self.message_id,
            "role": "user",
            "content": user_input
        })

        if "shitballs" in user_input.lower():
            await self.send_message(error_message, complete=False)
            await self.send_message("", complete=False)  # Send an empty message to keep connection open
            await self.rephrase_and_ask_question(self.script[self.current_step]['questions'][self.current_question], user_input)
            self.errors += 1
            return

        current_question = self.script[self.current_step]['questions'][self.current_question]
        question_text = current_question['question_text']

        # Define JSON schema for checking if the question is answered
        json_schema = {
            "type": "object",
            "properties": {
                "question_answered": {"type": "boolean"},
                "reasoning": {"type": "string"}
            },
            "required": ["question_answered", "reasoning"]
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"Question: {question_text}"},
            {"role": "user", "content": f"User's response: {user_input}"},
            {"role": "user", "content": f"Check if the user's response answers the question, which was: {question_text}. Follow this JSON schema: {json.dumps(json_schema, indent=2)}."}
        ]

        print(f"Formatted messages: {messages}")

        response_chunks = []
        async for chunk in my_generate(messages, stream=False, model=small_model):
            if chunk:
                response_chunks.append(chunk)

        response = ''.join(response_chunks).strip()
        print(f"Response: {response}")

        try:
            analysis = json.loads(response)
            question_answered = analysis.get("question_answered", False)
            reasoning = analysis.get("reasoning", "")
            print(f"Response Analysis: {analysis}")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            question_answered = False

        if not question_answered:
            await self.send_message(error_message, complete=False)
            await self.send_message("", complete=False)  # Send an empty message to keep connection open
            await self.rephrase_and_ask_question(current_question, user_input)
            self.errors += 1
            log_messages(chat_logger, {"Errors": self.errors})
            log_to_database(db, {
                "message_id": self.message_id,
                "errors": self.errors,
                "reasoning": reasoning
            })
            return

        if self.current_step < len(self.script):
            current_step = self.script[self.current_step]
            questions = current_step['questions']

            if question_answered and self.current_question < len(questions) - 1:
                self.current_question += 1
                await self.ask_question(questions[self.current_question])
            elif question_answered:
                self.current_step += 1
                self.current_question = 0
                if self.current_step < len(self.script):
                    await self.handle_next_step()
                else:
                    await self.send_message("End of script.", complete=True)
        else:
            await self.send_message("End of script.", complete=True)

    async def ask_question(self, question):
        question_text = question['question_text']
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Ask the following question, rephrasing as necessary so that it feels natural. Question: {question_text}."}
        ]

        response_text = ""
        async for chunk in my_generate(messages, stream=True, model=large_model):
            if chunk:
                response_text += chunk
        await self.send_message(response_text.strip(), complete=True)

    async def rephrase_and_ask_question(self, question, user_input):
        question_text = question['question_text']
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"{question_text}"},
            {"role": "user", "content": f"{user_input}"},
            {"role": "user", "content": f"Rephrase the original question ({question_text}) so it is a clear and appropriate response to what was just said ({user_input}). Make sure to phrase it as a question."}
        ]

        rephrased_question = ""
        async for chunk in my_generate(messages, stream=True, model=large_model):
            if chunk:
                rephrased_question += chunk
        await self.send_message(rephrased_question.strip(), complete=True)

    async def handle_next_step(self):
        next_step = self.script[self.current_step]
        step_text = ""
        await self.send_message(step_text, complete=True)
        await self.ask_question(next_step['questions'][self.current_question])

# ______________________________________________________________________________________________________________________________________________________________________________________________________________________________________________ #

# import json
# from config import system_prompt, script, error_message
# from my_generate import my_generate

# class WebSocketExecutor:
#     def __init__(self, ws):
#         self.ws = ws
#         self.chat_history = [{"role": "system", "content": system_prompt}]
#         self.current_step = 0
#         self.current_question = 0
#         self.script = script
#         self.message_id = 0

#     async def send_message(self, message, complete=False):
#         self.message_id += 1
#         self.chat_history.append({"role": "assistant", "content": message})
#         await self.ws.send_str(json.dumps({
#             "type": "response",
#             "data": message,
#             "complete": complete,
#             "message_id": self.message_id
#         }))

#     async def handle_input(self, user_input):
#         print(f"Handling user input: {user_input}")
#         self.chat_history.append({"role": "user", "content": user_input})

#         if "shitballs" in user_input.lower():
#             await self.send_message(error_message, complete=False)
#             await self.send_message("", complete=False)  # Send an empty message to keep connection open
#             await self.rephrase_and_ask_question(self.script[self.current_step]['questions'][self.current_question], user_input)
#             return

#         current_question = self.script[self.current_step]['questions'][self.current_question]
#         question_text = current_question['question_text']

#         # Define JSON schema for checking if the question is answered
#         json_schema = {
#             "type": "object",
#             "properties": {
#                 "question_answered": {"type": "boolean"},
#                 "reasoning": {"type": "string"}
#             },
#             "required": ["question_answered", "reasoning"]
#         }

#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "assistant", "content": f"Question: {question_text}"},
#             {"role": "user", "content": f"User's response: {user_input}"},
#             {"role": "user", "content": f"Check if the user's response answers the question, which was: {question_text}. Follow this JSON schema: {json.dumps(json_schema, indent=2)}."}
#         ]

#         print(f"Formatted messages: {messages}")

#         response_chunks = []
#         async for chunk in my_generate(messages, stream=False):
#             if chunk:
#                 response_chunks.append(chunk)

#         response = ''.join(response_chunks).strip()
#         print(f"Response: {response}")

#         try:
#             analysis = json.loads(response)
#             question_answered = analysis.get("question_answered", False)
#             reasoning = analysis.get("reasoning", "")
#             print(f"Response Analysis: {analysis}")
#         except json.JSONDecodeError as e:
#             print(f"JSONDecodeError: {e}")
#             question_answered = False

#         if not question_answered:
#             await self.send_message(error_message, complete=False)
#             await self.send_message("", complete=False)  # Send an empty message to keep connection open
#             await self.rephrase_and_ask_question(current_question, user_input)
#             return

#         if self.current_step < len(self.script):
#             current_step = self.script[self.current_step]
#             questions = current_step['questions']

#             if question_answered and self.current_question < len(questions) - 1:
#                 self.current_question += 1
#                 await self.ask_question(questions[self.current_question])
#             elif question_answered:
#                 self.current_step += 1
#                 self.current_question = 0
#                 if self.current_step < len(self.script):
#                     await self.handle_next_step()
#                 else:
#                     await self.send_message("End of script.", complete=True)
#         else:
#             await self.send_message("End of script.", complete=True)

#     async def ask_question(self, question):
#         question_text = question['question_text']
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Ask the following question, rephrasing as necessary so that it feels natural. Question: {question_text}."}
#         ]

#         response_text = ""
#         async for chunk in my_generate(messages, stream=True):
#             if chunk:
#                 response_text += chunk
#         await self.send_message(response_text.strip(), complete=True)

#     async def rephrase_and_ask_question(self, question, user_input):
#         question_text = question['question_text']
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "assistant", "content": f"{question_text}"},
#             {"role": "user", "content": f"{user_input}"},
#             {"role": "user", "content": f"Rephrase the original question ({question_text}) so it is a clear and appropriate response to what was just said ({user_input}). Make sure to phrase it as a question."}
#         ]

#         rephrased_question = ""
#         async for chunk in my_generate(messages, stream=True):
#             if chunk:
#                 rephrased_question += chunk
#         await self.send_message(rephrased_question.strip(), complete=True)

#     async def handle_next_step(self):
#         next_step = self.script[self.current_step]
#         step_text = ""
#         await self.send_message(step_text, complete=True)
#         await self.ask_question(next_step['questions'][self.current_question])

# ______________________________________________________________________________________________________________________________________________________________________________________________________________________________________________ #
# import json
# from config import system_prompt, script, error_message
# from my_generate import my_generate

# class WebSocketExecutor:
#     def __init__(self, ws):
#         self.ws = ws
#         self.chat_history = [{"role": "system", "content": system_prompt}]
#         self.current_step = 0
#         self.current_question = 0
#         self.script = script
#         self.message_id = 0

#     async def send_message(self, message, complete=False):
#         self.message_id += 1
#         self.chat_history.append({"role": "assistant", "content": message})
#         await self.ws.send_str(json.dumps({
#             "type": "response",
#             "data": message,
#             "complete": complete,
#             "message_id": self.message_id
#         }))

#     async def handle_input(self, user_input):
#         print(f"Handling user input: {user_input}")
#         self.chat_history.append({"role": "user", "content": user_input})

#         question_answered = "shitballs" not in user_input.lower()

#         if not question_answered:
#             await self.send_message(error_message, complete=False)
#             await self.send_message("", complete=False)  # Send an empty message to keep connection open
#             await self.rephrase_and_ask_question(self.script[self.current_step]['questions'][self.current_question], user_input)
#             return

#         if self.current_step < len(self.script):
#             current_step = self.script[self.current_step]
#             questions = current_step['questions']

#             if question_answered and self.current_question < len(questions) - 1:
#                 self.current_question += 1
#                 await self.ask_question(questions[self.current_question])
#             elif question_answered:
#                 self.current_step += 1
#                 self.current_question = 0
#                 if self.current_step < len(self.script):
#                     await self.handle_next_step()
#                 else:
#                     await self.send_message("End of script.", complete=True)
#         else:
#             await self.send_message("End of script.", complete=True)

#     async def ask_question(self, question):
#         question_text = question['question_text']
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Ask the following question, rephrasing as necessary so that it feels natural. Question: {question_text}."}
#         ]

#         response_text = ""
#         async for chunk in my_generate(messages, stream=True):
#             if chunk:
#                 response_text += chunk
#         await self.send_message(response_text.strip(), complete=True)

#     async def rephrase_and_ask_question(self, question, user_input):
#         question_text = question['question_text']
#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "assistant", "content": f"{question_text}"},
#             {"role": "user", "content": f"{user_input}"},
#             {"role": "user", "content": f"Rephrase the original question ({question_text}) so it is a clear and appropriate response to what was just said ({user_input}). Make sure to phrase it as a question."}
#         ]

#         rephrased_question = ""
#         async for chunk in my_generate(messages, stream=True):
#             if chunk:
#                 rephrased_question += chunk
#         await self.send_message(rephrased_question.strip(), complete=True)

#     async def handle_next_step(self):
#         next_step = self.script[self.current_step]
#         step_text = ""
#         await self.send_message(step_text, complete=True)
#         await self.ask_question(next_step['questions'][self.current_question])
