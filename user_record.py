import os
from langfuse.decorators import observe
from langfuse.openai import openai

@observe()
def read_user_record(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Creating a new file with default content.")
        default_content = """
# Client Record

## Client Information
**Name:** Jane Doe
**Age:** 30

## Alerts
_No alerts yet._

## Meal Preferences
_No meal preferences yet._

## Chat Records
- **Nutrition goal:** Not specified
- **Preferences:** Not specified
- **Cuisines:** Not specified
"""
        with open(file_path, "w") as file:
            file.write(default_content)
        return default_content

    with open(file_path, "r") as file:
        return file.read()

@observe()
def write_user_record(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

@observe()
def format_user_record(user_info, alerts, meal_preferences, chat_records):
    record = "# Client Record\n\n## Client Information\n"
    for key, value in user_info.items():
        record += f"**{key}:** {value}\n"
    
    record += "\n## Alerts\n"
    if alerts:
        for alert in alerts:
            record += f"- **{alert['date']}:** {alert['note']}\n"
    else:
        record += "_No alerts yet._\n"
    
    record += "\n## Meal Preferences\n"
    if meal_preferences:
        for preference in meal_preferences:
            record += f"- **{preference['date']}:** {preference['note']}\n"
    else:
        record += "_No meal preferences yet._\n"
    
    record += "\n## Chat Records\n"
    for key, value in chat_records.items():
        record += f"- **{key}:** {value}\n"
    
    return record

@observe()
def parse_user_record(markdown_content):
    user_info = {}
    alerts = []
    meal_preferences = []
    chat_records = {}
    
    current_section = None
    lines = markdown_content.split("\n")
    
    for line in lines:
        line = line.strip()  # Strip leading/trailing whitespace
        if line.startswith("## "):
            current_section = line[3:].strip()
        elif current_section == "Client Information" and line.startswith("**"):
            if ":** " in line:
                key, value = line.split(":** ", 1)
                key = key.strip("**").strip()
                value = value.strip()
                user_info[key] = value
        elif current_section == "Alerts":
            if "_No alerts yet._" in line:
                alerts = []
            elif line.startswith("- **"):
                if ":** " in line:
                    date, note = line.split(":** ", 1)
                    date = date.strip("- **").strip()
                    note = note.strip()
                    alerts.append({"date": date, "note": note})
        elif current_section == "Meal Preferences":
            if "_No meal preferences yet._" in line:
                meal_preferences = []
            elif line.startswith("- **"):
                if ":** " in line:
                    date, note = line.split(":** ", 1)
                    date = date.strip("- **").strip()
                    note = note.strip()
                    meal_preferences.append({"date": date, "note": note})
        elif current_section == "Chat Records" and line.startswith("- **"):
            if ":** " in line:
                key, value = line.split(":** ", 1)
                key = key.strip("- **").strip()
                value = value.strip()
                chat_records[key] = value
    
    final_record = {
        "Client Information": user_info,
        "Alerts": alerts,
        "Meal Preferences": meal_preferences,
        "Chat Records": chat_records
    }
    print(f"Final parsed record: {final_record}")
    return final_record