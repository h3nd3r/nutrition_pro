import json
from langfuse.decorators import observe
from langsmith import traceable

@traceable
@observe()
def traderjoes_items(scope=None):
    # read scraped json data from file and return it
    with open('data/traderjoes_items.json', 'r') as f:
        data = json.load(f)
    return data

#print(traderjoes_items())