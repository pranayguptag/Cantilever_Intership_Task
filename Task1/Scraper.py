# scraper.py (fix Myntra & Flipkart selectors)
import time, sqlite3, pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

DB_NAME = "ecommerce.db"
TABLE_NAME = "products"

def _init_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# ---------- Amazon ----------
def scrape_amazon(query, max_pages=1, headless=True):
    driver = _init_driver(headless)
    driver.get(f"https://www.amazon.in/s?k={query.replace(' ', '+')}")
    time.sleep(2)
    products = []
    for page in range(max_pages):
        items = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
        for item in items:
            try:
                title = item.find_element(By.TAG_NAME, "h2").text.strip()
            except: continue
            try:
                price = item.find_element(By.CSS_SELECTOR, ".a-price-whole").text
            except: price = "N/A"
            try:
                rating = item.find_element(By.CSS_SELECTOR, ".a-icon-alt").get_attribute("innerHTML")
            except: rating = "N/A"
            link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
            products.append({"Source":"Amazon","Title":title,"Price":price,"Rating":rating,"Link":link})
        try:
            driver.find_element(By.CSS_SELECTOR, "a.s-pagination-next").click()
            time.sleep(2)
        except: break
    driver.quit()
    return pd.DataFrame(products)

# ---------- Myntra ----------
def scrape_myntra(query, max_pages=1, headless=True):
    driver = _init_driver(headless)
    driver.get(f"https://www.myntra.com/{query.replace(' ', '-')}")
    time.sleep(2)
    products = []
    for page in range(max_pages):
        items = driver.find_elements(By.CSS_SELECTOR, ".product-base")
        for item in items:
            try:
                brand = item.find_element(By.CSS_SELECTOR, ".product-brand").text
                name = item.find_element(By.CSS_SELECTOR, ".product-product").text
                title = f"{brand} {name}"
            except: continue
            try:
                price = item.find_element(By.CSS_SELECTOR, ".product-price").text
            except: price = "N/A"
            link = item.find_element(By.TAG_NAME,"a").get_attribute("href")
            products.append({"Source":"Myntra","Title":title,"Price":price,"Rating":"N/A","Link":link})
        try:
            driver.find_element(By.CSS_SELECTOR,"li.pagination-next a").click()
            time.sleep(2)
        except: break
    driver.quit()
    return pd.DataFrame(products)

# ---------- Flipkart ----------
def scrape_flipkart(query, max_pages=1, headless=True):
    driver = _init_driver(headless)
    driver.get(f"https://www.flipkart.com/search?q={query.replace(' ', '+')}")
    time.sleep(2)
    products = []
    for page in range(max_pages):
        titles = driver.find_elements(By.CSS_SELECTOR,".IRpwTa, ._4rR01T")  # product titles
        prices = driver.find_elements(By.CSS_SELECTOR,"._30jeq3")           # prices
        links = driver.find_elements(By.CSS_SELECTOR,"a._1fQZEK, a.IRpwTa")
        for i in range(min(len(titles),len(prices),len(links))):
            products.append({"Source":"Flipkart","Title":titles[i].text,"Price":prices[i].text,
                             "Rating":"N/A","Link":links[i].get_attribute("href")})
        try:
            driver.find_element(By.CSS_SELECTOR,"a._1LKTO3").click()
            time.sleep(2)
        except: break
    driver.quit()
    return pd.DataFrame(products)

# ---------- DB Save & Clean ----------
def save_raw_to_db(df, reset=False):
    if df is None or df.empty: return
    conn=sqlite3.connect(DB_NAME)
    if reset: conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
    conn.close()

def clean_and_update_db():
    conn=sqlite3.connect(DB_NAME)
    try: df=pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    except: conn.close(); return
    if df.empty: conn.close(); return
    df["Price"]=df["Price"].astype(str).str.replace("₹","").str.replace(",","").str.extract(r"(\d+)")
    df["Price"]=pd.to_numeric(df["Price"],errors="coerce")
    df["Rating"]=pd.to_numeric(df["Rating"].astype(str).str.extract(r"(\d+\.\d+)")[0],errors="coerce")
    df=df.dropna(subset=["Price"]); df["Price"]=df["Price"].astype(float)
    conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
    conn.close()

def run_scrapers_and_update_db(query,use_amazon=False,use_myntra=False,use_flipkart=False,max_pages=1,headless=True):
    reset=True
    if use_amazon:
        save_raw_to_db(scrape_amazon(query,max_pages,headless),reset=reset); reset=False
    if use_myntra:
        save_raw_to_db(scrape_myntra(query,max_pages,headless),reset=reset); reset=False
    if use_flipkart:
        save_raw_to_db(scrape_flipkart(query,max_pages,headless),reset=reset); reset=False
    clean_and_update_db()
