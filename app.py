import base64
from dotenv import load_dotenv
import chainlit as cl
import openai
import asyncio
import json
from config import MODEL_CONFIGURATIONS, CONFIG_KEY
from datetime import datetime
from langfuse import Langfuse
from prompts import SYSTEM_PROMPT
from rag_pipeline import RAGPipeline
from functions.grocery_functions import get_location_id, get_grocery_items_on_promotion
from functions.scraper_functions import traderjoes_items
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from functions.tools import TOOLS
from recorder.assess import assess_message

# Load environment variables
load_dotenv()

# Get selected configuration
config = MODEL_CONFIGURATIONS[CONFIG_KEY]

langfuse = Langfuse()

client = wrap_openai(openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"]))
rag_pipeline = RAGPipeline()

gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

# Configuration setting to enable or disable the system prompt
ENABLE_SYSTEM_PROMPT = True

@traceable
def get_latest_user_message(message_history):
    # Iterate through the message history in reverse to find the last user message
    for message in reversed(message_history):
        if message['role'] == 'user':
            return message['content']
    return None

@traceable
async def generate_response(client, message_history, gen_kwargs):
    response_message = cl.Message(content="")
    await response_message.send()

    # Update here to check the response and call the API functions if needed
    # stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    stream = await client.chat.completions.create(
        messages=message_history,
        stream=True,
        tools=TOOLS,
        tool_choice="auto",
        **gen_kwargs
    )

    functions_called = {} # dictionary in the form of {index: {function_name: arguments}}

    async for part in stream:
        if part.choices[0].delta.tool_calls:
            tool_call = part.choices[0].delta.tool_calls[0]

            tool_call_index = tool_call.index
            function_name_delta = tool_call.function.name or ""
            arguments_delta = tool_call.function.arguments or ""
            function_name = functions_called.get(tool_call_index, {}).get("function_name", "")
            arguments = functions_called.get(tool_call_index, {}).get("arguments", "")
            function_name += function_name_delta
            arguments += arguments_delta

            functions_called.update({
                tool_call_index: {
                    "function_name": function_name,
                    "arguments": arguments
                }
            })

        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)

    await response_message.update()

    print("Functions called: ", functions_called)

    return response_message, functions_called

@traceable
@cl.on_message
async def on_message(message: cl.Message):
    print("on_message")
    message_history = cl.user_session.get("message_history", [])
    message_history.append({"role": "user", "content": message.content})

    # Processing images exclusively
    images = [file for file in message.elements if "image" in file.mime] if message.elements else []

    if images:
        print("image")        # Read the first image and encode it to base64
        with open(images[0].path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        print("DEBUG: base64_image size: ", len(base64_image))
        message_history.append({
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message.content
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ]
        })    

    # Send the message to the recorder to assess the message
    latest_message = get_latest_user_message(message_history)
    filtered_history = [msg for msg in message_history if msg['role'] != 'system']
    asyncio.create_task(assess_message(latest_message, filtered_history))

    response_message, functions_called = await generate_response(client, message_history, gen_kwargs)

    while functions_called: # handle one function call after another without new user message
        for _, tool_call_info in functions_called.items(): # handle multiple functions being returned in tool_calls
            function_name = tool_call_info.get("function_name", "")
            args = tool_call_info.get("arguments", "")
            print(f"DEBUG: in function_called for loop, function_name: {function_name}, args: {args}")

            if function_name == "get_grocery_items_on_promotion":
                print("calling get_grocery_items_on_promotion")
                args_dict = json.loads(args)
                location_id = args_dict.get('location_id', '')
                print("DEBUG: location_id: ", location_id)
                result = get_grocery_items_on_promotion(location_id)

            elif function_name == "get_location_id":
                print("calling get_location_id")
                args_dict = json.loads(args)
                zipcode = args_dict.get('zipcode', '')
                print("DEBUG: zipcode: ", zipcode)
                result = get_location_id(zipcode)

            elif function_name == "traderjoes_items":
                print("calling traderjoes_items")
                result = traderjoes_items()

            elif function_name == "get_favorite_recipes_from_message_history":
                print("calling get_favorite_recipes_from_message_history")
                result = rag_pipeline.query_user_favorite_recipes(message_history)

            else:
                result = f"Unknown function '{function_name}' cannot be called"

            # Append function call to the message history
            message_history.append({"role": "assistant", "content": f"Function call: {function_name}({args})"})

            # Append the function result to the message history
            message_history.append({"role": "system", "content": result})

            # Generate a new response incorporating the function results
            response_message, functions_called = await generate_response(client, message_history, gen_kwargs)

    # Record the AI's response in the history
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

@traceable
@cl.on_chat_start
async def on_chat_start():
    print("A new chat session has started!")
    message_history = cl.user_session.get("message_history", [])

    user_rag_data = rag_pipeline.retrieve_user_rag_data()
    message_history.insert(0, {"role": "system", "content": SYSTEM_PROMPT + user_rag_data})

    rag_pipeline.index_user_favorite_recipes()

    response_message,_ = await generate_response(client, message_history, gen_kwargs)

    # Record the AI's response in the history
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

    await response_message.send()

if __name__ == "__main__":
    cl.main()