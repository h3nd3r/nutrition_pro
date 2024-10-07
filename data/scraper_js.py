from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def load_page_with_js(url):
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)

    # Set up the WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Load the page
        driver.get(url)

        # Wait for JavaScript to execute (you might need to adjust the time)
        driver.implicitly_wait(10000)

        # Get the page source after JavaScript has run
        page_source = driver.page_source

        return page_source

    finally:
        # Always close the browser
        driver.quit()

# Example usage
url = 'https://www.traderjoes.com/home/products/category/food-8.model.json'
html_content = load_page_with_js(url)
print(html_content)