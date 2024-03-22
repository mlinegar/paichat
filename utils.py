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
