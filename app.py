import os
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
from rag_pipeline import retrieve_user_fre

# Load environment variables
load_dotenv()

# Get selected configuration
config = MODEL_CONFIGURATIONS[CONFIG_KEY]

langfuse = Langfuse()

# Initialize the OpenAI async client
client = openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"])

gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

# Configuration setting to enable or disable the system prompt
ENABLE_SYSTEM_PROMPT = True

def get_latest_user_message(message_history):
    # Iterate through the message history in reverse to find the last user message
    for message in reversed(message_history):
        if message['role'] == 'user':
            return message['content']
    return None

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
    print("Filled prompt: \n\n", filled_prompt)

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    assessment_output = response.choices[0].message.content.strip()
    print("Assessment Output: \n\n", assessment_output)

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

@cl.on_message
async def on_message(message: cl.Message):
    message_history = cl.user_session.get("message_history", [])

    if ENABLE_SYSTEM_PROMPT and (not message_history or message_history[0].get("role") != "system"):
        user_fre = retrieve_user_fre()
        system_prompt_content = SYSTEM_PROMPT + "\n" + user_fre  
        message_history.insert(0, {"role": "system", "content": system_prompt_content})

    message_history.append({"role": "user", "content": message.content})

    asyncio.create_task(assess_message(message_history))
    
    response_message = cl.Message(content="")
    await response_message.send()

    stream = await client.chat.completions.create(messages=message_history, stream=True, **gen_kwargs)
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await response_message.stream_token(token)

    # Record the AI's response in the history
    message_history.append({"role": "assistant", "content": response_message.content})
    cl.user_session.set("message_history", message_history)
    await response_message.update()

if __name__ == "__main__":
    cl.main()