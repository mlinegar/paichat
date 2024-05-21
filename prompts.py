import lmql
from lmql.lib.chat import message
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()
import logging

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""
    handler = logging.FileHandler(log_file, mode='w')        
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def log_messages(chat_logger, messages, level="info"):
    """
    Logs messages with specified logging level in a structured manner.

    Args:
    - chat_logger: The logger object.
    - messages: A dictionary where keys are message labels and values are the messages themselves.
    - level: The logging level as a string (e.g., "info", "error").
    """
    for label, value in messages.items():
        formatted_message = f"{label}: {value}"
        if level == "info" : 
            chat_logger.info(formatted_message)
        elif level == "error" : 
            chat_logger.error(formatted_message)
        # Add more logging levels here as needed.
            

@lmql.query(chunksize=16)
async def yes_no():
    '''lmql
    "Respond only with one of: 'Yes.' or 'No.'."
    "A:[FLAG]" #where STOPS_AT(FLAG, '.') # FLAG in ['Yes.', 'No.'] and 
    return "yes" in FLAG.lower()
    '''

@lmql.query
async def chain_of_thought():
    '''lmql
    "What needs to happen?"
    "Think through the question step by step.[THOUGHTS]"
    return THOUGHTS
    '''
        
# takes in and returns text
# used with @message to print text to the user without needing to invoke LLM
@lmql.query
async def print_text(text):
    '''lmql
    "{text}"
    '''

@lmql.query
async def include(text):
    '''lmql
    "Your response must include the following text verbatim: {text}"
    "[RESPONSE]"
    return RESPONSE
    '''

# FIXME: this is clumsy, and requires each tool individually to be added
@lmql.query(model=lmql.model('openai/gpt-4'))
async def use_tool(tool_name):
    '''lmql
    if tool_name == "immigration_story":
        "Recall a story from your training data that centers on the lived experience of an 'average' immigrant to the United States (for example: a refugee/asylum seeker, a farm worker, an undocumented parent)."
        "Our goal is to utilize perspective-sharing to reduce prejudice with regard to immigration, specifically, to reduce people's stated preference for large-scale arrests and detainment of immigrants at their place of work."
        "We want to recreate stories about immigration that volunteer canvassers might authentically share, stories that are personal, heartfelt, and real, designed to elicit sympathy and empathy for immigrants who would otherwise be arrested in mass detentions."
        "What types of personal stories will inspire empathy in the user?[COT: chain_of_thought]"
        "Now that you've thought about it, tell your story to the user."
    else:
        "ERROR: Tool not found."
    "[RESPONSE]"
    return RESPONSE
    '''

@lmql.query(model=lmql.model('openai/gpt-4'))
async def ask_question(question_text, last_response, user_response, verbatim, recalled_context="", max_length=256, tool_name=""):
    '''lmql
    "Reminder: the last thing you, the assistant, said was: {last_response}"
    if not user_response=="":
        "Reminder: the user said {user_response}."
    if not recalled_context=="":
        "Reminder: some information about the user: {recalled_context}."
    "Make sure to phrase what you say so that it feels like a natural response to what the user said."
    "Make sure your entire response will make sense to the user."
    if verbatim and tool_name =="":
        "Ask the user:[QUESTION: include(question_text)]"
    elif (not verbatim) and (not tool_name == ""):
        "[QUESTION: use_tool(tool_name)]"
    #  elif (not verbatim) and (tool_name == ""):
        #  "ERROR: Tool use requested but which tool was not specified. Explain the error.[QUESTION]"
    elif not verbatim:
        "Rephrase the following as a question to the user:{question_text}[QUESTION]" where len(TOKENS(QUESTION)) < max_length
    else: 
        # this should never happen
        "Rephrase the following as a question to the user:{question_text}[QUESTION]" where len(TOKENS(QUESTION)) < max_length
    return QUESTION
    '''

# option: switch from asking individual questions and stepping through
# to having all of the questions
# or: combine user answers for all questions in section into one response (ie is any of the info present)
@lmql.query(model=lmql.model('openai/gpt-3.5-turbo'))
async def analyze_question_answer(question_text, answer_text, prev_answer_text):
    '''lmql
    "Question: {question_text}"
    "User answer: {answer_text}"
    "Reminder: the user may be responding from their phone, so their responses may be short or incomplete. You should accept most user responses that are even vaguely relevant to the question."
    "There is a secret code: 'SKIP'. If the user says 'SKIP', then you should always accept this as a valid response."
    "We need to answer the following questions:"
    "1. Has the user answered the question, either in this response or a previous one?"
    "2. If the user did answer the question, what was their answer?"
    "3. If the user did answer the question, did they implicitly or explicitly ask for a follow up response? (e.g. 'I don't know', 'I need more information', 'I'm not sure', etc.)"
    "4. If the user did not answer the question, what was the reason?"
    "[COT: chain_of_thought]"
    "1. Has the user answered the question?[ANSWERED: yes_no]"
    if ANSWERED:
        "2. What was the user's answer?[ANSWER]"
        "3. Did the user ask for a follow up response?[FOLLOW_UP: yes_no]"
        ERR = ""
    else: 
        ANSWER = ""
        FOLLOW_UP = False
        "4. What does the user need to do next time to answer the question?[ERR]"
    return ANSWERED, ANSWER, FOLLOW_UP, ERR
    '''

# takes waaaaaay too long to run and too many tokens
@lmql.query(model=lmql.model('openai/gpt-3.5-turbo'))
async def what_next(question_context):
    '''lmql
    "Should we continue the current conversation or move on to the next question?"
    "Context: {question_context}"
    "We need to move through this survey quickly, but we also want the user to share their experiences and to show that we hear them."
    #  "Does the assistant need to respond to the user's last message rather than ask the next question?"
    #  "[COT: chain_of_thought]"
    #  "[ASSISTANT_RESPONSE_NEEDED: yes_no]"
    ASSISTANT_RESPONSE_NEEDED = True
    if ASSISTANT_RESPONSE_NEEDED:
        "Does the user seem engaged and wanting to continue this exact specific part of the conversation? (Assume no)"
        "[COT2: chain_of_thought]"
        "[USER_RESPONSE_NEEDED: yes_no]"
    else:
        USER_RESPONSE_NEEDED = False
    return ASSISTANT_RESPONSE_NEEDED, USER_RESPONSE_NEEDED
    '''
    
@lmql.query(model=lmql.model('openai/gpt-3.5-turbo'))
async def gen_flag(flag_text):
    '''lmql
    "{flag_text}"
    "[COT: chain_of_thought]"
    "[ANS: yes_no]"
    return ANS
    '''
    
def append_and_save(df, file_name):
    df = pd.concat([df, pd.DataFrame({'step_num': step_num, 'step_text': step_text, 'question_num': qq, 'tries' : 0, 'question_text': question_text, 'bot_output' : QUESTION, 'user_input': user_input, 'answer' : QUESTION_ANSWER}, index=[0])], ignore_index=True)
    df.to_csv(file_name)
    return df    