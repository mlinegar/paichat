import json
import copy
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
from config import system_prompt, script, error_message, large_model, small_model, max_tokens, MYTH, MYTH_ARTICLE, FACT, FACT_ARTICLE
from my_generate import my_generate

# chat_logic.py
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ChatLog

def log_to_database(db_session: Session, data):
    db_log = ChatLog(**data)
    db_session.add(db_log)
    db_session.commit()

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
# def log_to_database(db, data):
#     db.insert(data)
#     db.storage.flush()  # force save

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
        self.flag = None
        self.username = str(uuid.uuid4())  # Generate a unique username for this session
        self.chat_log_path = self.get_chat_log_path()
        self.db_session = SessionLocal()
        self.current_question_id = None
    
    # Ensure to close the session when done
    def __del__(self):
        self.db_session.close()    

    # async def end_script(self):
    #     end_message = "Thank you for participating!"
    #     await self.send_message(end_message, complete=True, end_script=True)
    async def end_script(self):
        end_message = "Thank you for participating! Please click the button in the top right corner to end the conversation."
        await self.send_message(end_message, complete=True, end_script=True)

    def get_chat_log_path(self):
        logs_dir = Path("chat_logs")
        logs_dir.mkdir(exist_ok=True)
        return logs_dir / f"{self.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    async def save_message(self, role, content):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {role}: {content}\n"
        with open(self.chat_log_path, "a") as f:
            f.write(log_entry)
    
    def get_last_assistant_message(self):
        for message in reversed(self.chat_history):
            if message["role"] == "assistant" and message["content"].strip():
                return message["content"]
        return None  # Return None if no non-empty assistant message is found

    async def send_message(self, message, complete=False, message_id=None, end_script=False):
        if message_id is None:
            self.message_id += 1
            message_id = self.message_id

        self.chat_history.append({"role": "assistant", "content": message})
        await self.save_message("assistant", message)
        response_data = {
            "message_id": message_id,
            "role": "assistant",
            "content": message,
            "complete": complete,
            "end_script": end_script,
            "user_id": self.username,
            "timestamp": datetime.now(),
            "step_number": self.current_step,
            "question_number": self.current_question,
            "question_id": self.current_question_id,
            "errors": self.errors,
            "flag": self.flag
        }

        await self.ws.send_str(json.dumps({
            "type": "response",
            "data": message,
            "complete": complete,
            "message_id": message_id,
            "end_script": end_script
        }))
        log_messages(chat_logger, {"Sent message": message})
        log_to_database(self.db_session, response_data)
        # response_data = {
        #     "type": "response",
        #     "data": message,
        #     "complete": complete,
        #     "message_id": message_id,
        #     "end_script": end_script
        # }

        # await self.ws.send_str(json.dumps(response_data))
        # log_messages(chat_logger, {"Sent message": message})
        # log_to_database(db, {
        #     "message_id": message_id,
        #     "role": "assistant",
        #     "content": message,
        #     "complete": complete,
        #     "end_script": end_script
        # })
    # async def send_message(self, message, complete=False, message_id=None, end_script=False):
    #     if message_id is None:
    #         self.message_id += 1
    #         message_id = self.message_id
    #     self.chat_history.append({"role": "assistant", "content": message})
    #     await self.save_message("assistant", message)
    #     response_data = {
    #         "type": "response",
    #         "data": message,
    #         "complete": complete,
    #         "message_id": message_id
    #     }
    #     if end_script:
    #         response_data["end_script"] = True
    #         response_data["redirect_url"] = "chat_assets/survey-complete.html"
    #     await self.ws.send_str(json.dumps(response_data))
    #     log_messages(chat_logger, {"Sent message": message})
    #     log_to_database(db, response_data)

    async def ask_question(self, question, direction=""):
        print(f"Inner: Current question: {question}")
        print(f"Inner: Current flag: {self.flag}")
        print(f"Inner: Flag required for question: {question.get('flag_required')}")
        print(f"Inner: Current number of errors: {self.errors}")
        self.current_question_id = question.get('question_id', '') 
        if question.get('flag_required', False) and self.flag != question.get('flag_required'):
            print(f"Skipping question due to flag mismatch. Required: {question.get('flag_required')}, Current: {self.flag}")
            await self.send_message("", complete=True)
        question_text = question['question_text']
        if question['verbatim']:
            verbatim_message = question_text
            # only truly verbatim if no errors
            if self.errors == 0:
                await self.send_message(verbatim_message, complete=True)
            else:
                full_chat_history = copy.copy(self.chat_history)
                # note: direct copy of below
                if not direction=="":
                    directed_message = f"Make absolutely no reference to this message other than to follow its instructions in your next message. Phrase your response as a direct response to what I (the user) just said. Make sure I (the user) have answered this question: {verbatim_message}. Additionally, follow this direction: {direction}"
                    full_chat_history.append({"role": "user", "content": directed_message})
                else:
                    question_message = f"Make absolutely no reference to this message other than to follow its instructions in your next message. Phrase your response as a direct response to what I (the user) just said. Make sure I (the user) have answered this question: {verbatim_message}."
                    full_chat_history.append({"role": "user", "content": question_message})
                # for testing
                # print(f"Full chat history: {full_chat_history}")
                response_text = ""
                # stream=True
                async for chunk in my_generate(full_chat_history, stream=False, model=large_model, max_tokens=max_tokens):
                    if chunk:
                        response_text += chunk
                        await self.send_message(response_text.strip(), complete=False)
                await self.send_message("", complete=True)
            # verbatim_message = ''
            # if self.errors > 0:
            #     verbatim_message += "I'm sorry, your last response didn't seem to answer the question. Could you please try again? As a reminder, this was the question I asked you:\n\n"
            # verbatim_message += question_text
            # await self.send_message(verbatim_message, complete=True)
        else:
            full_chat_history = copy.copy(self.chat_history)
            if question.get('use_tool', False):
                # get tool name with question.get('tool_name','')
                # this will be e.g. ARTICLE, which is a global variable defined in config.py
                tool_name = question.get('tool_name', '')
                if (not tool_name=="") and tool_name in globals():
                    tool_text = globals()[tool_name]
                    full_chat_history.append({"role": "system", "content": f"Use the following as context for your response. {tool_name}: {tool_text}"})
                    print(f"Using tool: {tool_name}")
                else:
                    print(f"Tool name not found: {tool_name}")
            if not direction=="":
                directed_message = f"Make absolutely no reference to this message other than to follow its instructions in your next message. Phrase your response as a direct response to what I (the user) just said. Additionally, follow this direction: {direction}"
                full_chat_history.append({"role": "user", "content": directed_message})
            question_message = f"Make absolutely no reference to this message other than to follow its instructions in your next message. Phrase your response as a direct response to what I (the user) just said. Make sure I (the user) have answered this question: {question_text}."
            full_chat_history.append({"role": "user", "content": question_message})
            # for testing
            # print(f"Full chat history: {full_chat_history}")
            response_text = ""
            # stream=True
            async for chunk in my_generate(full_chat_history, stream=False, model=large_model, max_tokens=max_tokens):
                if chunk:
                    response_text += chunk
                    await self.send_message(response_text.strip(), complete=False)
            await self.send_message("", complete=True)

    async def handle_input(self, user_input):
        print(f"Handling user input: {user_input}")
        try:
            current_question = self.script[self.current_step]['questions'][self.current_question]
        except IndexError:
            print("Reached end of script or encountered an out-of-range index")
            await self.end_script()
            return
        question_text = self.get_last_assistant_message()
        if question_text is None or not question_text.strip():
            question_text = self.script[self.current_step]['questions'][self.current_question]['question_text']
            og_question_text = ""
        else: 
            og_question_text = self.script[self.current_step]['questions'][self.current_question]['question_text']
        print(f"Last assistant message (question): {question_text}")
    
        self.chat_history.append({"role": "user", "content": user_input})
        await self.save_message("user", user_input)
        log_messages(chat_logger, {"User input": user_input})
        log_to_database(self.db_session, {
            "message_id": self.message_id,
            "role": "user",
            "content": user_input,
            "user_id": self.username,
            "timestamp": datetime.now(),
            "step_number": self.current_step,
            "question_number": self.current_question,
            "question_id": self.current_question_id,
            "errors": self.errors,
            "flag": self.flag
        })
        # log_to_database(db, {
        #     "message_id": self.message_id,
        #     "role": "user",
        #     "content": user_input
        # })

        current_question = self.script[self.current_step]['questions'][self.current_question]
        
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
        # Add flag property to schema if generate_flag is True
        if current_question.get('generate_flag', False):
            json_schema["properties"]['flag'] = {"type": "boolean"}
            json_schema["required"].append('flag')

        schema_guidance = f"""You are an AI assistant analyzing user input in a conversation.
            Since the user is on their phone, their responses may be short, incomplete, or contain typos.
            You should accept a wide range of responses as correct, as long as they attempt to answer the question.
            If the user does not want to answer or does not know, you should also accept that as a valid response.
            The only exception is if the user is asked a question that requires a numeric response.
            Given the question, user input, and previous responses, provide a JSON object with the following fields:
            - cot_reasoning: a brief chain-of-thought reasoning explaining your analysis
            - user_answered: true if the user's input attempts to answer any part of any question that was asked, false otherwise
            - move_to_next_q: usually true. True if the user's input even attempted to answer any part of any question that was asked, if they said they have not heard or do not know, if no follow-up question is needed, or in most cases, false otherwise, for example, if there seems to be a typo, or if the user asks a followup question
            - user_answer: the user's answer extracted from their input
            - numeric_answer: if the question requires a numeric response, extract the number from the user's input
            - assistant_response_needed: true if the assistant should provide a response before moving to the next question
            {f"- flag: true/false answer to {current_question['flag_text']}, based on the user's response" if current_question.get('generate_flag', False) else ""}
            Follow this JSON schema: {json.dumps(json_schema, indent=2)}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "assistant", "content": f"Question: {question_text}"},
            {"role": "user", "content": f"User's response: {user_input}"},
            {"role": "user", "content": f"Check if the user's response answers the question, which was: {question_text}. {schema_guidance}"}
        ]

        structured_output = ""
        async for chunk in my_generate(messages, model=small_model, schema=json_schema, stream=False, max_tokens=max_tokens):
            # print(f"Output chunk: {chunk}")
            structured_output += chunk
        
        try:
            analysis = json.loads(structured_output)
            user_answered = analysis.get("user_answered", True)
            move_to_next_q = analysis.get("move_to_next_q", True)
            reasoning = analysis.get("cot_reasoning", "")
            print(f"Response Analysis: {analysis}")
            # Set self.flag if generate_flag is True
            if current_question.get('generate_flag', False):
                flag_text = current_question['flag_text']
                self.flag = analysis.get('flag', False)
                print(f"Flag question: {flag_text}. Flag set: {self.flag}")
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            move_to_next_q = True
            user_answered = True
            reasoning = ""
            self.flag = None
            self.errors = 0
        
        if (user_answered==False and current_question.get('requires_user_answer',False)==True) or not move_to_next_q:
            self.errors += 1
            direction_addendum = ""
            if (user_answered==False and current_question.get('requires_user_answer',False)==True):
                direction_addendum += "Tell the user their previous response didn't seem to answer the question. "
            if not move_to_next_q:
                direction_addendum += " Give a complete and coherent response to whatever the user just said. If the user's previous response contained a typo or seems in appropriate, apologize to the user, tell them why their response didn't seem to answer the question. Otherwise, respond to the user's message naturally, responding to what they said in the context of your conversation. Repeat yourself as little as possible, telling the user to refer to your last message if necessary. "
            if og_question_text=="":
                og_question_addendum = ""
            else:
                og_question_addendum = f" Remember, the original question that we actually want to get an answer to was: '{og_question_text}'. We expect the user to respond to that. Privately, we want to answer the question: '{question_text}', if the user has not already answered it."
            direction = f"Respond to the user's message. {direction_addendum} , ask them to read your last message, then rephrase the key parts of the question itself and ask it again.{og_question_addendum} If necessary, explain why the user's last message was rejected (the reasoning was: {reasoning}). This said, do not repeat your last message, except where strictly necessary. Guide the user to answer the important parts of the question with your response. Respond to any and all questions or points of confusion they may have. Focus your response on the user's last message, and make sure to respond to it in a way that makes sense in the context of the conversation. Again, do not repeat your previous message except where absolutely necessary to ask a question."
            await self.ask_question(current_question, direction=direction)
            log_messages(chat_logger, {"Errors": self.errors})
            log_to_database(self.db_session, {
                "message_id": self.message_id,
                "errors": self.errors,
                "reasoning": reasoning,
                "user_id": self.username,
                "timestamp": datetime.now(),
                "step_number": self.current_step,
                "question_number": self.current_question,
                "flag": self.flag
            })
            # log_to_database(db, {
            #     "message_id": self.message_id,
            #     "errors": self.errors,
            #     "reasoning": reasoning
            # })
        else:
            self.errors = 0
            await self.move_to_next_question()

    async def move_to_next_question(self):
        self.current_question += 1
        if self.current_question >= len(self.script[self.current_step]['questions']):
            self.current_step += 1
            self.current_question = 0
            self.errors = 0 # Reset errors at the end of each step
            self.flag = None  # Reset flag at the end of each step
            print(f"End of Step {self.current_step - 1}. Flag reset to None.")

        if self.current_step < len(self.script):
            await self.handle_next_step()
        else:
            await self.send_message("Thank you for participating!", complete=True, end_script=True)

    async def handle_next_step(self):
        try:
            while self.current_step < len(self.script):
                current_step = self.script[self.current_step]
                questions = current_step['questions']
                print(f"Step {current_step} of {len(questions)}")

                while self.current_question < len(questions):
                    question = questions[self.current_question]
                    flag_required = question.get('flag_required')
                    print(f"Outer: Question id: {question.get('question_id')}")
                    print(f"Outer: Current step: {self.current_step}, Current question: {self.current_question}")
                    print(f"Outer: Flag required for question: {flag_required}")
                    print(f"Outer: Current flag: {self.flag}")

                    if flag_required is not None:
                        if self.flag != flag_required:
                            print(f"Skipping question due to flag mismatch. Required: {flag_required}, Current: {self.flag}")
                            self.current_question += 1
                            continue
                    
                    print(f"Asking question: {question['question_text']}")
                    await self.ask_question(question)
                    return  # Exit and wait for user input

                # Move to next step if we've gone through all questions
                self.current_step += 1
                self.current_question = 0
                self.flag = None
                self.errors = 0
                print(f"Moving to step {self.current_step}. Flag reset to None.")
            # If we've reached this point, we've completed all steps
            await self.end_script()
        except IndexError:
            print("Encountered an out-of-range index while processing the script")
            await self.end_script()
