import json
import os
import requests
from dotenv import load_dotenv
from langfuse.decorators import observe
from requests.auth import HTTPBasicAuth

# for testing - temp until we have a better way to get location id (ticket #3)
GROCERY_LOCATION_IDS = {
    "Bellevue-QFC": "70500822",
    "Vancouver-FredMeyer": "70100140",
}

API_SCOPE = {
    "product": "product.compact"
}

@observe()
def get_access_token(scope=None):
    load_dotenv()
    client_id = os.getenv('KROGER_CLIENT_ID')
    client_secret = os.getenv('KROGER_CLIENT_SECRET')
    token_url = os.getenv('KROGER_TOKEN_ENDPOINT')
    auth = HTTPBasicAuth(client_id, client_secret)

    if scope is None:
        data = {'grant_type': 'client_credentials'}
    else:
        data = {'grant_type': 'client_credentials', 'scope': scope}

    response = requests.post(token_url, auth=auth, data=data)

    if response.status_code != 200:
        raise Exception(f"Error: Failed to get access token: {response.status_code}")
    
    try:
        token_data = response.json()
        if 'access_token' in token_data:
            return token_data['access_token']
        else:
            raise Exception(f"Error: Access token not found in response: {token_data}")
    except json.JSONDecodeError:
        raise Exception(f"Error: Failed to decode JSON {response.text}")

@observe()
def get_grocery_items(location_id, num_items_limit=10):
    try:
        access_token = get_access_token(scope=API_SCOPE['product'])
    except Exception as e:
        return f"Error: Failed to get access token: {e}, cannot get grocery items"
    
    url = f'https://api.kroger.com/v1/products'
    params = {
        'filter.term': 'produce',
        'filter.locationId': location_id,
        'filter.fulfillment': 'csp',
        'filter.limit': num_items_limit
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return f"Error: Failed to get grocery items: {response.status_code}"

    try:
        response_data = response.json()
        if 'data' in response_data:
            items = [item['description'] for item in response_data['data']]
            formatted_items = ", ".join(items)
            print(f"Grocery items: {formatted_items}")
            return f"Here are some grocery items you might want to buy: {formatted_items}"
        else:
            print(f"Error: No data found in response {response_data}")
            return "No grocery items found in the nearby grocery stores"
    except Exception as e:
        print(f"Error: Failed to get grocery items: {e}")
        return "No grocery items found in the nearby grocery stores"

# To test the function, uncomment the following line:
# print(get_grocery_items(num_items_limit=20, location_id=GROCERY_LOCATION_IDS['Bellevue-QFC']))