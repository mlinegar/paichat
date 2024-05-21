import json
import os
import openai
import logging
import asyncio
from datetime import datetime
import uuid
from pathlib import Path
from tinydb import TinyDB, JSONStorage
from tinydb.middlewares import CachingMiddleware
from tenacity import retry, stop_after_attempt, wait_random_exponential
from config import system_prompt, script, error_message, large_model, small_model, max_tokens
from my_generate import my_generate

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setting up database and logger
# Generate the date-time string
current_time = datetime.now().strftime('%Y%m%d_%H%M')
user_id = str(uuid.uuid4())
path = Path(f"output/{current_time}_{user_id}.db")
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
        self.flags = {}  # Dictionary to store flags

    async def send_message(self, message, complete=False, message_id=None):
        if message_id is None:
            self.message_id += 1
            message_id = self.message_id
        self.chat_history.append({"role": "assistant", "content": message})
        await self.ws.send_str(json.dumps({
            "type": "response",
            "data": message,
            "complete": complete,
            "message_id": message_id
        }))
        log_messages(chat_logger, {"Sent message": message})
        log_to_database(db, {
            "message_id": message_id,
            "role": "assistant",
            "content": message,
            "complete": complete
        })

    async def ask_question(self, question, direction=""):
        print(f"Current question: {question}")
        question_text = question['question_text']
        if question['verbatim']:
            await self.send_message(question_text, complete=True)
        else:
            full_chat_history = self.chat_history + [
                {"role": "user", "content": f"Make absolutely no reference to this message other than to follow its instructions. Phrase your response as a direct response to what I just said. Make sure I have answered this question: {question_text}.{direction}"}
            ]

            response_text = ""
            async for chunk in my_generate(full_chat_history, stream=True, model=large_model, max_tokens=max_tokens):
                if chunk:
                    response_text += chunk
                    await self.send_message(response_text.strip(), complete=False)
            await self.send_message("", complete=True)

    async def handle_input(self, user_input):
        print(f"Handling user input: {user_input}")
        self.chat_history.append({"role": "user", "content": user_input})
        log_messages(chat_logger, {"User input": user_input})
        log_to_database(db, {
            "message_id": self.message_id,
            "role": "user",
            "content": user_input
        })

        current_question = self.script[self.current_step]['questions'][self.current_question]
        question_text = current_question['question_text']
        q_max_tokens = current_question.get("max_tokens", max_tokens)

        json_schema = {
            "type": "object",
            "properties": {
                "cot_reasoning": {"type": "string"},
                "user_answered": {"type": "boolean"},
                "move_to_next_q": {"type": "boolean"},
                "user_answer": {"type": "string"},
                "numeric_answer": {"type": "number"},
                "assistant_response_needed": {"type": "boolean"}
            },
            "required": ["move_to_next_q", "user_answered", "user_answer", "assistant_response_needed", "cot_reasoning"]
        }
        schema_guidance = f"""You are an AI assistant analyzing user input in a conversation.
            Since the user is on their phone, their responses may be short, incomplete, or contain typos.
            You should accept a wide range of responses as correct, as long as they attempt to answer the question.
            If the user does not want to answer or does not know, you should also accept that as a valid response.
            The only exception is if the user is asked a question that requires a numeric response.
            Given the question, user input, and previous responses, provide a JSON object with the following fields:
            - cot_reasoning: a brief chain-of-thought reasoning explaining your analysis
            - user_answered: true if the user's input answers the question, false otherwise
            - move_to_next_q: true if the user's input answers the question or if no follow-up question is needed, false otherwise
            - user_answer_summary: the user's answer extracted from their input
            - numeric_answer: if the question requires a numeric response, extract the number from the user's input
            - assistant_response_needed: true if the assistant should provide a response before moving to the next question
            Follow this JSON schema: {json.dumps(json_schema, indent=2)}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"Question: {question_text}"},
            {"role": "user", "content": f"User's response: {user_input}"},
            {"role": "user", "content": f"Check if the user's response answers the question, which was: {question_text}. {schema_guidance}"}
        ]

        structured_output = ""
        async for chunk in my_generate(messages, model=small_model, schema=json_schema, stream=False, max_tokens=max_tokens):
            print(f"Output chunk: {chunk}")
            structured_output += chunk
        
        try:
            analysis = json.loads(structured_output)
            user_answered = analysis.get("user_answered", True)
            move_to_next_q = analysis.get("move_to_next_q", True)
            reasoning = analysis.get("cot_reasoning", "")
            print(f"Response Analysis: {analysis}")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            move_to_next_q = True
            user_answered = True
            reasoning = ""

        if not move_to_next_q:
            # await self.send_message(error_message, complete=False)
            # await self.send_message("", complete=False)  # Send an empty message to keep connection open
            if user_answered:
                await self.ask_question(current_question, direction=f"Respond to the user's message.")
            else: 
                await self.ask_question(current_question, direction=f"Respond to the user's message, making sure that question: '{question_text}' is gets asked, and explaining why the user's last message was rejected (the reasoning was: {reasoning}).")

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

            if move_to_next_q and self.current_question < len(questions) - 1:
                self.current_question += 1
                await self.ask_question(questions[self.current_question])
            elif move_to_next_q:
                self.current_step += 1
                self.current_question = 0
                if self.current_step < len(self.script):
                    await self.handle_next_step()
                else:
                    await self.send_message("End of script.", complete=True)
        else:
            await self.send_message("End of script.", complete=True)

    async def handle_next_step(self):
        next_step = self.script[self.current_step]
        step_text = next_step['step_text']
        questions = next_step['questions']

        for question in questions:
            if question['flag_required']:
                flag_text = question['flag_text']
                if not self.flags.get(flag_text, False):
                    continue  # Skip this question if the flag is not true

            await self.ask_question(question)
            if question['requires_user_answer']:
                break  # Stop asking questions until the current question is answered
