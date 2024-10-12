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
from recorder.recorder_prompt import RECORDER_PROMPT
from recorder.user_record import read_user_record, write_user_record, format_user_record, parse_user_record
from langsmith.wrappers import wrap_openai
from langsmith import traceable
from functions.tools import TOOLS

# Load environment variables
load_dotenv()

# Get selected configuration
config = MODEL_CONFIGURATIONS[CONFIG_KEY]

langfuse = Langfuse()

client = wrap_openai(openai.AsyncClient(api_key=config["api_key"], base_url=config["endpoint_url"]))

gen_kwargs = {
    "model": config["model"],
    "temperature": 0.3,
    "max_tokens": 500
}

@traceable
async def assess_message(latest_message, filtered_history):
    print("DEBUG: Assessing message")
    file_path = "user/user_record.md"
    markdown_content = read_user_record(file_path)
    parsed_record = parse_user_record(markdown_content)

    # Convert message history, dinner log, meal preferences, and chat records to strings
    history_str = json.dumps(filtered_history, indent=4)
    dinner_log_str = json.dumps(parsed_record.get("Dinner Log", []), indent=4)
    meal_preferences_str = json.dumps(parsed_record.get("Meal Preferences", []), indent=4)
    chat_records_str = json.dumps(parsed_record.get("Chat Records", {}), indent=4)
    
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Generate the assessment prompt for the recorder
    filled_prompt = RECORDER_PROMPT.format(
        latest_message=latest_message,
        history=history_str,
        existing_dinner_log=dinner_log_str,
        existing_meal_preferences=meal_preferences_str,
        existing_chat_records=chat_records_str,
        current_date=current_date
    )

    response = await client.chat.completions.create(messages=[{"role": "system", "content": filled_prompt}], **gen_kwargs)

    assessment_output = response.choices[0].message.content.strip()

    # Parse the assessment output
    dinner_log_updates, meal_preferences_updates, chat_records_updates = parse_assessment_output(assessment_output)

    # Update the user record with the new dinner log updates, meal preferences updates and chat records updates
    parsed_record["Dinner Log"].extend(dinner_log_updates)
    parsed_record["Meal Preferences"].extend(meal_preferences_updates)
    for update in chat_records_updates:
        topic = update["topic"]
        note = update["note"]
        parsed_record["Chat Records"][topic] = note

    # Format the updated record and write it back to the file
    updated_content = format_user_record(
        parsed_record["Client Information"],
        parsed_record["Dinner Log"],
        parsed_record["Meal Preferences"],
        parsed_record["Chat Records"]
    )
    write_user_record(file_path, updated_content)

@traceable
def parse_assessment_output(output):
    try:
        parsed_output = json.loads(output)
        dinner_log_updates = parsed_output.get("dinner_log_updates", [])
        meal_preferences_updates = parsed_output.get("meal_preferences_updates", [])
        chat_records_updates = parsed_output.get("chat_records_updates", [])
        return dinner_log_updates, meal_preferences_updates, chat_records_updates
    except json.JSONDecodeError as e:
        print("Failed to parse assessment output:", e)
        return [], [], []