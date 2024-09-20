import os

# Model configurations - add more as needed
MODEL_CONFIGURATIONS = {
    "openai_gpt-4o": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o"
    }
}