import json
from langfuse.decorators import observe
from langsmith import traceable
import random

@traceable
@observe()
def traderjoes_items(scope=None):
    # read scraped json data from file and return it
    with open('data/traderjoes_items.json', 'r') as json_file:
        data = json.load(json_file)
        items = random.sample(data, 10)
    return json.dumps(items)

#print(traderjoes_items())