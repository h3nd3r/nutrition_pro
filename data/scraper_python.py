# scraper-python.py
# To run this script, paste `python scraper-python.py` in the terminal

import httplib2
import requests
from bs4 import BeautifulSoup, SoupStrainer

def scrape():
    #url = 'https://www.traderjoes.com/home/products/category/food-8'
    url = 'https://www.traderjoes.com/home/products/category/food-8.model.json'

    response = requests.get(url)
    print(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup)

    http = httplib2.Http()
    status, response = http.request(url)
    for link in BeautifulSoup(response, 'html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            print(link['href'])
'''
    title = soup.select_one('h1')
    links = soup.find_all('a')
    print(title)
    for link in links:
        print(link.get('href'))
'''
if __name__ == '__main__':
    scrape()