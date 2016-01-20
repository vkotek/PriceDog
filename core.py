from bs4 import BeautifulSoup
import requests, re

# List of product URLs to scan prices for. Supports Heureka.cz only.
url = [
    "http://mobilni-telefony.heureka.cz/apple-iphone-5s-16gb/",
    "http://mobilni-telefony.heureka.cz/huawei-honor-7-16gb/",
    "http://mobilni-telefony.heureka.cz/lenovo-p70/"]

# List of shops to scan prices for. This ID can be found in the URL of the 'koupit' hyperlink on Heureka.
shops = ['czc-cz','mall-cz','alza-cz']

# Scraping function scans 'urls' list and collects prices for items in 'shops' list.
# Returns list in format [product:[]
def scraperito(urls, shops):

    results = [] # Setup empty list where dictionaries of products will be stored
    
    # Product/URL loop
    for url in urls:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        # Get fancy product name
        item_name = soup.h1.string
        
        # Find button with price and shop name code
        items = soup.select("a.pricen")

        # RESULTS = [{productA:[{shopA1:priceA1},{shop2:price2}]},{productB:[{shopB1:priceB1},{shopB2:priceB2}]}]
        prices = {} 
        result = { item_name : prices } # 
        
        # Go through each buy button, check if link is in shop list, convert price to int, append to results.
        for item in items:
            for shop in shops:
                if shop in item.get('href'):
                    prices[shop] = re.sub("[^0-9]","",item.text)
        results.append(result)
    return results

final = scraperito(url, shops)

print(final)
