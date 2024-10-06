import os

# Model configurations - add more as needed
MODEL_CONFIGURATIONS = {
    "openai_gpt-4o-mini": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o-mini-2024-07-18"
    },
    "openai_gpt-4o": {
        "endpoint_url": os.getenv("OPENAI_ENDPOINT"),
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": "gpt-4o"
    }
}

# Choose configuration
CONFIG_KEY = "openai_gpt-4o-mini"
