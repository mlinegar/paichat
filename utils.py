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

# This python script is meant to provide an example of how WashU API endpoints can
# be accessed. 
import requests
import os
from requests.auth import HTTPBasicAuth
import time

def get_access_token(url, client_id, client_secret, scope):
    payload = {
        'grant_type': 'client_credentials',
        'scope': scope
    }
    timeout_duration = 10  # Timeout in seconds
    try:
        start_time = time.time()
        response = requests.post(url, auth=HTTPBasicAuth(client_id, client_secret), data=payload, timeout=timeout_duration)
        end_time = time.time()
        response.raise_for_status()
        print(f"Access token request duration: {end_time - start_time} seconds")
        return response.json()['access_token']
    except requests.RequestException as e:
        print(f"Failed to get access token: {e}")
        return None
    except ValueError:  # Includes simplejson.decoder.JSONDecodeError
        print("Failed to parse JSON response")
        return None

def post_data(api_url, token, data):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    try:
        start_time = time.time()
        response = requests.post(api_url, json=data, headers=headers)
        end_time = time.time()
        print(f"API request duration: {end_time - start_time} seconds", response)
        if response.status_code == 401:
            error_message = response.json().get('message', '')
            if "Access Token is missing or invalid" in error_message:
                print("Token expired. Fetching a new token...")
                token = get_access_token(token_url, client_id, client_secret, scope)
                if token:
                    return post_data(api_url, token, data)  # Retry with new token
                else:
                    return "Failed to refresh token."
        elif response.status_code == 403:
            print("Response is a 403 error code. You may be receiving this error code if you are not on WashU's network or VPN.")
        elif response.status_code == 402:
            print("Response is a 402 error code. You may be receiving this error code if have exceed the budget of your account.")
            print("Please contact di2accelerator@wustl.edu for assistance.")                
        elif response.status_code == 418:
            print("Response is a 418 error code. You may be receiving this error code if more than 10 calls a second has been performed.")
            print("Please contact di2accelerator@wustl.edu for assistance.")         
        elif response.status_code != 200:
            return response.text
        
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to post data: {e}")
        return None
