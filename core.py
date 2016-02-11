#!/usr/bin/python
# coding: utf-8

try:
    from bs4 import BeautifulSoup
    import ConfigParser as cp
    import requests, re, sys
    import MySQLdb as sql
except Val:
    print "Error importing modules, exiting."
    exit()
    

# Import database credentials from secured config file
config = cp.RawConfigParser()
config.read('/var/www-secret/config.ini')
db_user = config.get('database','username')
db_pass = config.get('database','password')
db_name = config.get('database','database')


# Open database connection
db = sql.connect("localhost",db_user,db_pass,db_name)
# prepare db cursor
cursor = db.cursor()

def db_getproducts():
    # List of product URLs to scan prices for. Supports Heureka.cz only.
    # gets list of products, each item is (id,url)
    cursor.execute("SELECT id,code,name FROM products")
    products = cursor.fetchall() 
    return products

def db_getshops():
    # This version of beta uses the shop_link table, allowing each product to use different shops
    BETA_args = """
    SELECT shops.code
    FROM shops
    LEFT JOIN shop_link
    ON shops.id = shop_link.shop_id
    WHERE shop_link.product_id = ???
    """
    # For now, lets use all shops for all products.
    args = """
    SELECT id,code
    FROM shops
    """
    cursor.execute(args)
    shops = cursor.fetchall()
    print "Shops from DB: ", shops
    return shops

# Scraping function scans 'urls' list and collects prices for items in 'shops' list.
# Returns list in format [product:[]
def db_getprices(products):

    results = [] # Setup empty list where dictionaries of products will be stored
    results_sql = []
    db_shops = db_getshops()

    # Product/URL loop
    for product in products:

        shops = list(db_shops)
        # Get list of shops
        # shops = db_getshops()
        
        # Get html data from products page
        url = product[1] + "?expand=1#!o=4"
        html = requests.get(url).text
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
                if shop[1] in item.get('href'):
                    shops.pop(shops.index(shop))
                    price = re.sub("[^0-9]","",item.text)
                    # product ID, shop ID, date, price
                    result = (product[0],shop[0],price)
                    results_sql.append(result)
    return results_sql

def db_insertprices(data):
    
    # Prepare general statement for insertin data from array
    stmt = """
    INSERT INTO prices(product_id, shop_id, date, price)
    VALUES (%s,%s,CURDATE(),%s)
    """
    # Try to insert data into DB
    try:
        print data
        cursor.executemany(stmt, data)
        db.commit()
        print "New prices successfuly inserted into database"
    except:
        db.rollback()

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
    print "%s has been added." % item_name
    return    

def cron():
    # Get prices for products for all shops
    data = db_getprices(db_getproducts())
    # Insert prices into DB
    db_insertprices(data)
    
def add_product():
    db_addproduct(sys.argv[2])
    
def help():
    print """
    core.py [option] [arg]
    
    [option]:
        add_product     - Add new product, requires [arg] with URL of Heureka page
        cron            - Cron task to get prices and insert them into DB
        dev		- Runs a test scrape, prints prices to terminal only.
    """

def dev():
    data = db_getproducts()
    print data
    data2 = db_getprices(data)
    print data2

if __name__ == '__main__':
    globals()[sys.argv[1]]()

#new_product = str(raw_input("Heureka URL:"))
#db_addproduct(new_product)
