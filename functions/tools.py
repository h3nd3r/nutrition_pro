TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_grocery_items_on_promotion",
            "description": "Call this to get the grocery items on promotion at client's local grocery store, as specified by the location id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location_id": {
                        "type": "string",
                        "description": "The location id of the client's local grocery store.",
                    },
                },
                "required": ["location_id"],
                "additionalProperties": False,
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_location_id",
            "description": "Call this to get the location id of the client's local grocery store, as specified by the zipcode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zipcode": {
                        "type": "string",
                        "description": "The zipcode to get the location id for.",
                    },
                },
                "required": ["zipcode"],
                "additionalProperties": False,
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_favorite_recipes_from_message_history",
            "description": "Call this if user asks to get a list of favorite recipes from the client's Notion workspace using the message history as context.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        }
    },  
    {
        "type": "function",
        "function": {
            "name": "traderjoes_items",
            "description": "Call this to get a list of items from trader joes.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        }
    },
]

