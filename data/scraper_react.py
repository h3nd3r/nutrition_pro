from playwright.sync_api import sync_playwright
import time
import json
import pdb

def scrape_react_page(url):
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        '''
        # test against local html file
        file_path = 'traderjoes.html'

        # Open the file and read its contents
        with open(file_path, 'r', encoding='utf-8') as file:
            file_contents = file.read()
        page.set_content(file_contents)
        '''
        # Wait for a specific element that indicates the React app has loaded
        page.wait_for_selector('.ProductCard_card__title__text__uiWLe')

        # You might need to interact with the page
        # page.click('button.load-more')

        # Wait a bit for any animations or additional loading
        time.sleep(2)

        #print(page.content())
        # Extract data
        elements = page.query_selector_all('.ProductCard_card__title__text__uiWLe')
        data = []
        for element in elements:
            title = element.query_selector('.Link_link__1AZfr').inner_text()
            link = "https://www.traderjoes.com" + element.query_selector('.Link_link__1AZfr').get_attribute('href')
            data.append({"title": title, "link": link})
        browser.close()
        #json_array = json.dumps(data)
        return data

# Usage
url = "https://www.traderjoes.com/home/products/category/food-8"
scraped_data = scrape_react_page(url)

with open('traderjoes_items.json', 'w', encoding='utf-8') as json_file:
    json.dump(scraped_data, json_file, ensure_ascii=False, indent=4)  # indent for pretty printing
#print(scraped_data)