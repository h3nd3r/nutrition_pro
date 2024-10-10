import os
import base64
from dotenv import load_dotenv
import chainlit as cl
import openai
import asyncio
import json
from config import MODEL_CONFIGURATIONS, CONFIG_KEY
from datetime import datetime
from langfuse import Langfuse
from prompts import ASSESSMENT_PROMPT, SYSTEM_PROMPT
from user_record import read_user_record, write_user_record, format_user_record, parse_user_record
from rag_pipeline import RAGPipeline
from functions.grocery_functions import get_grocery_items, get_location_id, get_grocery_items_on_promotion
from functions.scraper_functions import traderjoes_items
from functions.notion_reader import retrieve_random_page_content
import re
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from functions.tools import TOOLS

# Load environment variables
load_dotenv()

# Get selected configuration
config = MODEL_CONFIGURATIONS[CONFIG_KEY]

langfuse = Langfuse()

# Initialize the OpenAI async client
#client = openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"])
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
async def assess_message(message_history):
    file_path = "user/user_record.md"
    markdown_content = read_user_record(file_path)
    parsed_record = parse_user_record(markdown_content)

    latest_message = get_latest_user_message(message_history)

    # Remove the original prompt from the message history for assessment
    filtered_history = [msg for msg in message_history if msg['role'] != 'system']

    # Convert message history, alerts, meal preferences, and chat records to strings
    history_str = json.dumps(filtered_history, indent=4)
    alerts_str = json.dumps(parsed_record.get("Alerts", []), indent=4)
    meal_preferences_str = json.dumps(parsed_record.get("Meal Preferences", []), indent=4)
    chat_records_str = json.dumps(parsed_record.get("Chat Records", {}), indent=4)
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate the assessment prompt
    filled_prompt = ASSESSMENT_PROMPT.format(
        latest_message=latest_message,
        history=history_str,
        existing_alerts=alerts_str,
        existing_meal_preferences=meal_preferences_str,
        existing_chat_records=chat_records_str,
        current_date=current_date
    )    
    # print("Filled prompt: \n\n", filled_prompt)

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    assessment_output = response.choices[0].message.content.strip()
    # print("Assessment Output: \n\n", assessment_output)

    # Parse the assessment output
    new_alerts, new_meal_preferences, chat_records_updates = parse_assessment_output(assessment_output)

    # Update the user record with the new alerts, new meal preferences and chat records updates
    parsed_record["Alerts"].extend(new_alerts)
    parsed_record["Meal Preferences"].extend(new_meal_preferences)
    for update in chat_records_updates:
        topic = update["topic"]
        note = update["note"]
        parsed_record["Chat Records"][topic] = note

    # Format the updated record and write it back to the file
    updated_content = format_user_record(
        parsed_record["Client Information"],
        parsed_record["Alerts"],
        parsed_record["Meal Preferences"],
        parsed_record["Chat Records"]
    )
    write_user_record(file_path, updated_content)

@traceable
def parse_assessment_output(output):
    try:
        parsed_output = json.loads(output)
        new_alerts = parsed_output.get("new_alerts", [])
        new_meal_preferences = parsed_output.get("meal_preferences_updates", [])
        chat_records_updates = parsed_output.get("chat_records_updates", [])
        return new_alerts, new_meal_preferences, chat_records_updates
    except json.JSONDecodeError as e:
        print("Failed to parse assessment output:", e)
        return [], [], []

@traceable
def extract_json(content):
    # Regular expression to find the JSON blob
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        json_str = match.group(0)  # Extract the matched JSON string
        try:
            # Attempt to parse the JSON to ensure it's valid
            json_data = json.loads(json_str.strip())
            return json_data  # Return the parsed JSON object
        except json.JSONDecodeError:
            print("Error: Extracted string is not valid JSON.")
            return None  # Return None if JSON is invalid
    print("No JSON blob found.")
    return None  # Return None if no match is found

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

    asyncio.create_task(assess_message(message_history))

    response_message, functions_called = await generate_response(client, message_history, gen_kwargs)

    #function_call = extract_json(response_message.content)
    #print(f"Extracting function from response: {function_call}")
    # while function_call and "function_name" in function_call and "args" in function_call:

    while functions_called: # handle one function call after another without new user message
        for _, tool_call_info in functions_called.items(): # handle multiple functions being returned in tool_calls
            function_name = tool_call_info.get("function_name", "")
            args = tool_call_info.get("arguments", "")

            print("in function_call if block")
            # function_name = function_call["function_name"]
            # args = function_call["args"]

            if function_name == "get_grocery_items":
                print("calling get_grocery_items")
                args_dict = json.loads(args)
                location_id = args_dict.get('location_id', '')

                print("DEBUG: location_id: ", location_id)

                result = get_grocery_items(location_id)
            elif function_name == "get_grocery_items_on_promotion":
                print("calling get_grocery_items_on_promotion")
                args_dict = json.loads(args)
                location_id = args_dict.get('location_id', '')
                
                print("DEBUG: location_id: ", location_id)
                
                result = get_grocery_items_on_promotion(location_id)
            elif function_name == "get_location_id":
                print("calling get_location")
                args_dict = json.loads(args)
                zipcode = args_dict.get('zipcode', '')
                
                print("DEBUG: zipcode: ", zipcode)
                
                result = get_location_id(zipcode)
            elif function_name == "get_random_favorite_recipe":
                print("calling get_random_favorite_recipe")
                result = retrieve_random_page_content()
            elif function_name == "traderjoes_items":
                print("calling traderjoes_items")
                result = traderjoes_items()
            elif function_name == "get_favorite_recipes_from_message_history":
                print("calling get_favorite_recipes_from_message_history")
                #print("DEBUG: message_history in function call: ", message_history)
                result = rag_pipeline.query_user_favorite_recipes(message_history)
            else:
                result = f"Unknown function '{function_name}' cannot be called"

            # Append function call to the message history
            message_history.append({"role": "assistant", "content": f"Function call: {function_name}({args})"})

            # Append the function result to the message history
            message_history.append({"role": "system", "content": result})

            # Generate a new response incorporating the function results
            response_message, functions_called = await generate_response(client, message_history, gen_kwargs)
            # should we update message history with response message here?

            # function_call = extract_json(response_message.content)

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

    response_message, functions_called = await generate_response(client, message_history, gen_kwargs)

    # Record the AI's response in the history
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)

    await response_message.send()

if __name__ == "__main__":
    cl.main()