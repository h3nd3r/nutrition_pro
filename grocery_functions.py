import os
import requests
from langfuse.decorators import observe
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from requests.auth import HTTPBasicAuth
import json
import base64

from dotenv import load_dotenv

# for testing
GROCERY_LOCATION_IDS = {
    "Bellevue-QFC": "70500822",
    "Vancouver-FredMeyer": "70100140",
}

@observe()
def get_access_token():
    load_dotenv()

    client_id = os.getenv('KROGER_CLIENT_ID')
    client_secret = os.getenv('KROGER_CLIENT_SECRET')
    token_url = os.getenv('KROGER_TOKEN_ENDPOINT')
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {base64.b64encode(f"{os.getenv('KROGER_CLIENT_ID')}:{os.getenv('KROGER_CLIENT_SECRET')}".encode()).decode()}'
    }
    data = 'grant_type=client_credentials&scope=product.compact'
    token= json.loads(requests.post(token_url, headers=headers, data=data).text)
    return token['access_token']
    


    # auth = HTTPBasicAuth(client_id, client_secret)
    # client = BackendApplicationClient(client_id=client_id)
    # oauth = OAuth2Session(client=client)
    # token = oauth.fetch_token(token_url=token_url, client_id=client_id, client_secret=client_secret)
    
    # return token['access_token']

print(get_access_token())

def generate_request():
    

    url = f"https://api.kroger.com/v1/connect/oauth2/token"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {os.getenv('TMDB_API_ACCESS_TOKEN')}"
    }

    response = requests.get(url, headers=headers)
    cart_data = response.json()
    return cart_data

@observe()
def get_grocery_items(limit=5, location_id=None):
    # url = f"https://api.kroger.com/v1/locations/{location_id}/cart/items"
    # headers = {
    #     "accept": "application/json",
    #     "Authorization": f"Bearer {os.getenv('TMDB_API_ACCESS_TOKEN')}"
    # }

    # response = requests.get(url, headers=headers)
    # cart_data = response.json()
    # return cart_data
    #return "Strawberries, Celery, Apples, Carrots, Onions"

    access_token = get_access_token()
    url = 'https://api.kroger.com/v1/products?filter.term=produce&filter.locationId=01400943&filter.fulfillment=csp&filter.limit=10'
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = json.loads(requests.get(url, headers=headers).text)
    descriptions = list(map(lambda item: item['description'], response['data']))
    # response_items = response['data']
    # return response_items
    #print(response)
    return descriptions

print(get_grocery_items())





