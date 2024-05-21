import asyncio
import os
from openai import AsyncOpenAI
import json

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def format_prompt(messages, model_name):
    if "gpt" in model_name.lower():
        return messages
    else:
        formatted_messages = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            formatted_messages.append({"role": role, "content": content})
        return formatted_messages
    
async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, schema=None, stream=False):
    formatted_messages = format_prompt(messages, model)
    print(f"Formatted messages: {formatted_messages}")

    collected_text = ""

    try:
        if schema is None:
            response = await client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=stream
            )
        else:
            response = await client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                functions=[{"name": "json_test", "parameters": schema}],
                function_call="auto",
                stream=stream
            )

        if stream:
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    if hasattr(choice.delta, 'content') and choice.delta.content is not None:
                        chunk_content = choice.delta.content
                        collected_text += chunk_content
                        # print(f"Stream chunk: {chunk_content}")
        else:
            if hasattr(response.choices[0], 'message'):
                message = response.choices[0].message
                if hasattr(message, 'content') and message.content is not None:
                    collected_text = message.content
                elif hasattr(message, 'function_call') and message.function_call and hasattr(message.function_call, 'arguments') and message.function_call.arguments:
                    collected_text = message.function_call.arguments
                else:
                    print("Error: Unexpected response structure or content missing.")
                    collected_text = "Sorry, I encountered an error while processing your request."
            else:
                print("Error: Response does not contain 'message'.")
                collected_text = "Sorry, I encountered an error while processing your request."
        
        final_output = collected_text.strip()
        print(f"Final output: {final_output}")
        yield final_output

    except Exception as e:
        print(f"Error processing messages: {str(e)}")
        yield "Sorry, I encountered an error while processing your request."

# Test function
async def test_my_generate():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "test"}
    ]
    
    async for chunk in my_generate(messages, stream=True):
        print(f"Output chunk: {chunk}")

async def test_my_generate_with_schema():
    json_schema = {
        "type": "object",
        "properties": {
            "cot_reasoning": {"type": "string"},
            "user_answered": {"type": "boolean"},
            "user_answer": {"type": "string"},
            "numeric_answer": {"type": "number"},
            "assistant_response_needed": {"type": "boolean"}
        },
        "required": ["user_answered", "user_answer", "assistant_response_needed", "cot_reasoning"]
    }
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": "On a scale of 0 to 10, how do you feel about universal healthcare?"},
        {"role": "user", "content": "I feel it's an 8."},
        {"role": "user", "content": f"Check if the user's response answers the question. Follow this schema:{json.dumps(json_schema)}"}
    ]
    
    final_output = ""
    async for chunk in my_generate(messages, model="gpt-3.5-turbo", schema=json_schema, stream=False):
        print(f"Output chunk: {chunk}")
        final_output += chunk
    
    return final_output

# # Run the test function
# gen_test = asyncio.run(test_my_generate())
# # print(f"Generation test result: {gen_test}")
# schema_gen_test = asyncio.run(test_my_generate_with_schema())
# print(f"Did the schema test run successfully? {json.loads(schema_gen_test)['user_answered']}")


# import os
# from openai import AsyncOpenAI

# client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def format_prompt(messages, model_name):
#     if "gpt" in model_name.lower():
#         return messages
#     else:
#         formatted_messages = []
#         for message in messages:
#             role = message["role"]
#             content = message["content"]
#             formatted_messages.append({"role": role, "content": content})
#         return formatted_messages

# async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, schema=None, stream=False):
#     formatted_messages = format_prompt(messages, model)
#     print(f"Formatted messages: {formatted_messages}")

#     try:
#         if schema is None:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 stream=stream
#             )
#         else:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 functions=[{"name": "json_test", "parameters": schema}],
#                 function_call="auto",
#                 stream=stream
#             )

#         if stream:
#             async for chunk in response:
#                 if "choices" in chunk and chunk["choices"]:
#                     if "delta" in chunk["choices"][0] and "content" in chunk["choices"][0]["delta"]:
#                         chunk_content = chunk["choices"][0]["delta"]["content"]
#                         print(f"Stream chunk: {chunk_content}")
#                         yield chunk_content
#         else:
#             full_response = response.choices[0].message['content']
#             print(f"Response: {full_response}")
#             yield full_response
#     except Exception as e:
#         print(f"Error processing messages: {str(e)}")
#         yield "Sorry, I encountered an error while processing your request."

# import os
# from openai import AsyncOpenAI

# client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def format_prompt(messages, model_name):
#     if "gpt" in model_name.lower():
#         return messages
#     else:
#         formatted_messages = []
#         for message in messages:
#             role = message["role"]
#             content = message["content"]
#             formatted_messages.append(f"{role}: {content}")
#         return "\n".join(formatted_messages)

# async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, schema=None, stream=False):
#     formatted_messages = format_prompt(messages, model)
#     print(f"Formatted messages: {formatted_messages}")

#     try:
#         if schema is None:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 stream=stream
#             )
#         else:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 functions=[{"name": "json_test", "parameters": schema}],
#                 function_call="auto",
#                 stream=stream
#             )

#         if stream:
#             async for chunk in response:
#                 if "choices" in chunk and chunk["choices"]:
#                     if "delta" in chunk["choices"][0] and "content" in chunk["choices"][0]["delta"]:
#                         chunk_content = chunk["choices"][0]["delta"]["content"]
#                         print(f"Stream chunk: {chunk_content}")
#                         yield chunk_content
#         else:
#             full_response = response.choices[0].message['content']
#             print(f"Response: {full_response}")
#             yield full_response
#     except Exception as e:
#         print(f"Error processing messages: {str(e)}")
#         yield "Sorry, I encountered an error while processing your request."

# import os
# from openai import OpenAI
# from transformers import AutoTokenizer

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def format_prompt(messages, model_name):
#     if "gpt" in model_name.lower():
#         return messages
#     else:
#         formatted_messages = []
#         for message in messages:
#             role = message["role"]
#             content = message["content"]
#             formatted_messages.append(f"{role}: {content}")
#         return "\n".join(formatted_messages)

# async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, tokenizer=None, schema=None, stream=False):
#     formatted_messages = format_prompt(messages, model)
#     print(f"Formatted messages: {formatted_messages}")

#     try:
#         if schema is None:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 stream=stream
#             )
#         else:
#             response = await client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 functions=[{"name": "json_test", "parameters": schema}],
#                 function_call="auto",
#                 stream=stream
#             )

#         if stream:
#             async for chunk in response:
#                 if chunk.choices[0].delta.content:
#                     chunk_content = chunk.choices[0].delta.content
#                     print(f"Stream chunk: {chunk_content}")
#                     yield chunk_content
#                 if chunk.choices[0].finish_reason == 'stop':
#                     print("Stream finished.")
#                     break
#         else:
#             full_response = response.choices[0].message['content']
#             print(f"Response: {full_response}")
#             yield full_response
#     except Exception as e:
#         print(f"Error processing messages: {str(e)}")
#         yield "Sorry, I encountered an error while processing your request."

# import os
# from openai import OpenAI
# from transformers import AutoTokenizer

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def format_prompt(messages, model_name):
#     if "gpt" in model_name.lower():
#         return messages
#     else:
#         formatted_messages = []
#         for message in messages:
#             role = message["role"]
#             content = message["content"]
#             formatted_messages.append(f"{role}: {content}")
#         return "\n".join(formatted_messages)

# async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, tokenizer=None, schema=None, stream=False):
#     formatted_messages = format_prompt(messages, model)
#     print(f"Formatted messages: {formatted_messages}")

#     try:
#         if schema is None:
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 stream=stream
#             )
#         else:
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 functions=[{"name": "json_test", "parameters": schema}],
#                 function_call="auto",
#                 stream=stream
#             )

#         if stream:
#             collected_chunks = []
#             async for chunk in response:
#                 if chunk.choices[0].delta.content:
#                     chunk_content = chunk.choices[0].delta.content
#                     collected_chunks.append(chunk_content)
#                     print(f"Stream chunk: {chunk_content}")
#                     yield chunk_content
#                 if chunk.choices[0].finish_reason == 'stop':
#                     print("Stream finished.")
#                     break
#         else:
#             full_response = response.choices[0].message['content']
#             print(f"Response: {full_response}")
#             yield full_response
#     except Exception as e:
#         print(f"Error processing messages: {str(e)}")
#         yield "Sorry, I encountered an error while processing your request."

# import os
# from openai import OpenAI
# from transformers import AutoTokenizer

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# def format_prompt(messages, model_name):
#     if "gpt" in model_name.lower():
#         return messages
#     else:
#         formatted_messages = []
#         for message in messages:
#             role = message["role"]
#             content = message["content"]
#             formatted_messages.append(f"{role}: {content}")
#         return "\n".join(formatted_messages)

# async def my_generate(messages, model="gpt-3.5-turbo", temperature=0.7, max_tokens=256, top_p=1.0, frequency_penalty=0.0, presence_penalty=0.0, tokenizer=None, schema=None, stream=False):
#     formatted_messages = format_prompt(messages, model)
#     print(f"Formatted messages: {formatted_messages}")

#     try:
#         if schema is None:
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 stream=stream
#             )
#         else:
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=formatted_messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens,
#                 top_p=top_p,
#                 frequency_penalty=frequency_penalty,
#                 presence_penalty=presence_penalty,
#                 functions=[{"name": "json_test", "parameters": schema}],
#                 function_call="auto",
#                 stream=stream
#             )

#         if stream:
#             collected_chunks = []
#             collected_messages = []
#             for chunk in response:
#                 collected_chunks.append(chunk)
#                 chunk_message = chunk.choices[0].delta.content
#                 if chunk_message:
#                     collected_messages.append(chunk_message)
#                     print(f"Stream chunk: {chunk_message}")
#                     yield chunk_message
#         else:
#             print(f"Response: {response.choices[0].message['content']}")
#             yield response.choices[0].message['content']
#     except Exception as e:
#         print(f"Error processing messages: {str(e)}")
#         yield "Sorry, I encountered an error while processing your request."
