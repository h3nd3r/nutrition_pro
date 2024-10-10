import json
import os
import requests
from dotenv import load_dotenv
from langfuse.decorators import observe
from requests.auth import HTTPBasicAuth
from langsmith import traceable

API_SCOPE = {
    "product": "product.compact"
}

@traceable
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


@traceable
@observe()
def get_grocery_items_request(location_id, num_items_limit):
    try:
        access_token = get_access_token(scope=API_SCOPE['product'])
    except Exception as e:
        raise Exception(f"Error: Failed to get access token: {e}, cannot get grocery items")
    
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
        raise Exception(f"Error: Failed to get grocery items: {response.status_code}")

    try:
        response_data = response.json()
        if 'data' in response_data:
            return response_data['data']
        else:
            raise Exception(f"Error: No 'data' found in grocery response {response_data}")
    except Exception as e:
        raise Exception(f"Error: Failed to get grocery items: {e}")

@traceable
@observe()
# 50 is the max number of items that can be returned by the API unless we paginate
def get_grocery_items_on_promotion(location_id, num_items_limit=50):
    try:
        data = get_grocery_items_request(location_id, num_items_limit)

        promoted_items = []
        for product in data:
            if 'items' in product and product['items']:
                item = product['items'][0]
                if 'price' in item:
                    regular_price = item['price'].get('regular', 0)
                    promo_price = item['price'].get('promo', 0)
                    if promo_price and promo_price != 0 and promo_price < regular_price: # if there's no promo, promo_price will be 0
                        promoted_items.append({
                            'description': product['description'],
                            'regular_price': regular_price,
                            'promo_price': promo_price
                        })

        if promoted_items:
            formatted_items = ", ".join([f"{item['description']} (Regular: ${item['regular_price']:.2f}, Promo: ${item['promo_price']:.2f})" for item in promoted_items])
            print(f"Grocery items on promotion: {formatted_items}")
            return f"Here are some grocery items on promotion: {formatted_items}"
        else:
            return "No grocery items on promotion found in the nearby grocery stores"
    except Exception as e:
        print(f"Error: Failed to get grocery items on promotion: {e}")
        return "Failed to get grocery items on promotion in the nearby grocery stores"

@traceable
@observe()
def get_location_id(zipcode):

    try:
        access_token = get_access_token()
    except Exception as e:
        return f"Error: Failed to get access token: {e}, cannot get local store"
    
    url = f'https://api.kroger.com/v1/locations'
    params = {
        'filter.zipCode.near': zipcode,
        'filter.limit': '1',
        'filter.department': '69' # online ordering
    }
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return f"Error: Failed to find location near {zipcode} with code: {response.status_code}"

    try:
        response_data = response.json()
        location_ids = [location['locationId'] for location in response_data['data']]
        return f" The locationId of your nearest store is: {location_ids[0]}"

    except Exception as e:
        print(f"Error: Failed to get local grocery store with exception {e}")
        return None

# To test the function, uncomment the following line:
# get_grocery_items_on_promotion(num_items_limit=50, location_id=70100140)
#print(get_location_id(zipcode=98006))