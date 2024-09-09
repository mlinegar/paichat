import json
import os

max_depth = 2
script_name = "immigration_uhc_script_v3"
external_port = 20113
internal_port = 8089
host = '0.0.0.0'
system_prompt = "You are a helpful assistant."
# error_message = "Your answer doesn't seem to address the question appropriately. Could you please try again?"
error_message = ""
initial_message = "Hi! I'm Brook, a volunteer canvasser. What's your name?"
# small_model = "gpt-3.5-turbo"
small_model = "gpt-4o-mini"
large_model = "gpt-4o"
max_tokens = 1500
# Load script
print(f"Loading script: {script_name}")
with open(f'data/{script_name}.json') as f:
    full_script = json.load(f)
    script_details = full_script[0]
    script_description = script_details['script_description']
    script_length = len(full_script)
    script = full_script[1:script_length]
