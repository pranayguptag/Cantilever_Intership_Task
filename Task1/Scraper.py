from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import sqlite3


# ---------- AMAZON SCRAPER ----------
def scrape_amazon(search_query="shoes", max_pages=2):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = f"https://www.amazon.in/s?k={search_query.replace(' ', '+')}"
    driver.get(url)
    time.sleep(3)

    products = []

    for page in range(max_pages):
        items = driver.find_elements(By.XPATH, "//div[@data-component-type='s-search-result']")
        for item in items:
            try:
                title = item.find_element(By.TAG_NAME, "h2").text.strip()
                try:
                    price = item.find_element(By.CLASS_NAME, "a-price-whole").text.strip()
                except:
                    price = "N/A"
                try:
                    rating = item.find_element(By.CLASS_NAME, "a-icon-alt").get_attribute("innerHTML").strip()
                except:
                    rating = "N/A"
                link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                products.append(["Amazon", title, price, rating, link])
            except:
                continue

        # go to next page
        try:
            next_btn = driver.find_element(By.CLASS_NAME, "s-pagination-next")
            next_btn.click()
            time.sleep(3)
        except:
            break

    driver.quit()
    return pd.DataFrame(products, columns=["Source", "Title", "Price", "Rating", "Link"])


# ---------- MYNTRA SCRAPER ----------
def scrape_myntra(search_query="shoes", max_pages=2):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = f"https://www.myntra.com/{search_query.replace(' ', '-')}"
    driver.get(url)
    time.sleep(3)

    products = []

    for page in range(max_pages):
        items = driver.find_elements(By.CLASS_NAME, "product-base")
        for item in items:
            try:
                brand = item.find_element(By.CLASS_NAME, "product-brand").text.strip()
                product_name = item.find_element(By.CLASS_NAME, "product-product").text.strip()
                title = f"{brand} {product_name}"

                try:
                    price = item.find_element(By.CLASS_NAME, "product-discountedPrice").text.strip()
                except:
                    try:
                        price = item.find_element(By.CLASS_NAME, "product-price").text.strip()
                    except:
                        price = "N/A"

                link = item.find_element(By.TAG_NAME, "a").get_attribute("href")
                products.append(["Myntra", title, price, "N/A", link])
            except:
                continue

        # go to next page
        try:
            next_btn = driver.find_element(By.XPATH, "//li[@class='pagination-next']/a")
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(3)
        except:
            break

    driver.quit()
    return pd.DataFrame(products, columns=["Source", "Title", "Price", "Rating", "Link"])


# ---------- SAVE TO SQLITE ----------
def save_to_sqlite(df, db_name="ecommerce.db", table_name="products", reset=False):
    conn = sqlite3.connect(db_name)
    if reset:
        conn.execute(f"DELETE FROM {table_name}")  # clear old rows
        conn.commit()
    df.to_sql(table_name, conn, if_exists="append", index=False)
    conn.close()



# ---------- RUN SCRAPERS ----------
if __name__ == "__main__":
    amazon_df = scrape_amazon("shoes", max_pages=2)
    myntra_df = scrape_myntra("shoes", max_pages=2)

    # Reset first, then save Amazon & Myntra
    save_to_sqlite(amazon_df, reset=True)  
    save_to_sqlite(myntra_df)

    print("Amazon Scraped:", amazon_df.shape)
    print("Myntra Scraped:", myntra_df.shape)
    print("✅ Fresh Data saved to ecommerce.db (only shoes)")
