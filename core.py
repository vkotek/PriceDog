#!/usr/bin/python

from bs4 import BeautifulSoup
import requests, re
import MySQLdb as sql

# Open database connection
db = sql.connect("localhost","pricedog","14B9Rsjsi2","pricedog")
# prepare db cursor
cursor = db.cursor()

def db_getproducts():
    # List of product URLs to scan prices for. Supports Heureka.cz only.
    # gets list of products, each item is (id,url)
    cursor.execute("SELECT id,code,name FROM products")
    products = cursor.fetchall() 
    return products

url = [
    "http://mobilni-telefony.heureka.cz/apple-iphone-5s-16gb/",
    "http://mobilni-telefony.heureka.cz/huawei-honor-7-16gb/",
    "http://mobilni-telefony.heureka.cz/lenovo-p70/"]

# List of shops to scan prices for. This ID can be found in the URL of the 'koupit' hyperlink on Heureka.
shops = ['czc-cz','mall-cz','alza-cz']

def db_getshops(product):
    # This version of beta uses the shop_link table, allowing each product to use different shops
    BETA_args = """
    SELECT shops.code
    FROM shops
    LEFT JOIN shop_link
    ON shops.id = shop_link.shop_id
    WHERE shop_link.product_id = 1
    """
    # For now, lets use all shops for all products.
    args = """
    SELECT code
    FROM shops
    """
    cursor.execute(args)
    shops = cursor.fetchall()
    return shops

# Scraping function scans 'urls' list and collects prices for items in 'shops' list.
# Returns list in format [product:[]
def db_getprices(products):

    results = [] # Setup empty list where dictionaries of products will be stored
    
    # Product/URL loop
    for product in products:
        
        # Get shops for product
        shops = db_getshops(product[0])
        
        # Get html data from products page
        html = requests.get(product[1]).text
        soup = BeautifulSoup(html, 'html.parser')

        # Get fancy product name
        item_name = soup.h1.string
        
        # Find button with price and shop name code
        items = soup.select("a.pricen")

        # RESULTS = [{productA:[{shopA1:priceA1},{shop2:price2}]},{productB:[{shopB1:priceB1},{shopB2:priceB2}]}]
        prices = {} 
        result = { item_name : prices }
        
        # Go through each buy button, check if link is in shop list, convert price to int, append to results.
        for item in items:
            for shop in shops:
                if shop[0] in item.get('href'):
                    prices[shop] = re.sub("[^0-9]","",item.text)
        results.append(result)
    print results
    return results

def db_addproduct(url):
    # Add a new product to the list by passing its Heureka URL.
    
    # Get html data from url and parse it
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')

    # Get fancy product name
    item_name = soup.h1.string
    
    # Get current products to check if already exists
    product = [product[2] for product in db_getproducts()]
    
    if item_name in product:
        print "This product is already in the list"
        return
    print "I should'be be here"
    
    # If it isnt, lets continue
    sql = """
    INSERT INTO products(code,name)
    VALUES ("%s", "%s")
    """ % (url, item_name)
    
    # Try to execute and commit
    try:
        cursor.execute(sql)
        db.commit()
    except: # Rollback if shit hits the fan
        db.rollback()
    

db_getprices(db_getproducts())
#db_addproduct(url)
