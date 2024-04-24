import time
import datetime
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def create_products_table(conn):
    try:
        # SQL command to create the products table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS Levis_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255),
            price VARCHAR(50),
            discounted_price VARCHAR(50),
            discount VARCHAR(50),
            image_url TEXT,
            color VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        print('Table created successfully')
    except sqlite3.Error as e:
        print('Error:', e)
    finally:
        if 'cursor' in locals():
            cursor.close()

def insert_product_details(conn, product_data):
    try:
        # Insert the product details into the database
        cursor = conn.cursor()
        insert_query = "INSERT INTO Levis_products (name, price, discounted_price, discount, image_url, color) VALUES (?, ?, ?, ?, ?, ?)"
        cursor.execute(insert_query, product_data)
        conn.commit()
        cursor.close()
    except sqlite3.Error as e:
        print('Error:', e)

def scrape_color_info(driver):
    try:
        # Wait for the color details to be present on the page
        wait = WebDriverWait(driver, 20)
        color_fieldset = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'js.product-form__input')))  

        # Find the color span within the color fieldset
        color_span = color_fieldset.find_element(By.CSS_SELECTOR, 'span[id^="selected-color-template"]')

        # Extract the color text
        color = color_span.text.strip() if color_span else "N/A"

        return color

    except Exception as e:
        print('Error:', e)
        return "N/A"

def scrape_product_details(url):
    try:
        # Initialize the Chrome webdriver
        driver = webdriver.Chrome()  # Make sure you have chromedriver installed and its path set correctly

        driver.maximize_window()

        # Load the webpage
        driver.get(url)
        
        print(f"[{datetime.datetime.now()}] Webpage loaded.")

        # Wait for dynamic content to load
        wait = WebDriverWait(driver, 20)  # Increase wait time
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))

        print(f"[{datetime.datetime.now()}] Dynamic content loaded.")

        # Get initial product count
        last_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))

        # Scroll down slowly to load more products
        while True:
            # Scroll to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Adjust the pause time between scrolls

            # Wait for new products to load
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))
            new_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))

            # If no new products are loaded, break the loop
            if new_count == last_count:
                break

            last_count = new_count

        print(f"[{datetime.datetime.now()}] All products loaded.")

        # Parse the HTML content of the webpage
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all product elements on the page
        product_elements = soup.find_all('div', class_='product-card')

        if not product_elements:
            # If product card structure is not found, try alternative class
            product_elements = soup.find_all('div', class_='product-card__info')

        # Connect to the SQLite database
        try:
            conn = sqlite3.connect('db.sqlite3')

            if conn is not None:
                print(f"[{datetime.datetime.now()}] Connected to SQLite database")
                create_products_table(conn)

                # Iterate over each product element and extract details
                for product_element in product_elements:
                    # Extract product name
                    name_element = product_element.find('a', class_='product-card__title')
                    name = name_element.text.strip() if name_element else 'N/A'

                    # Extract product price
                    price_element = product_element.find('span', class_='tw-font-bold')
                    price = price_element.text.strip() if price_element else 'N/A'

                    # Extract discounted price
                    discounted_price_element = product_element.find('span', class_='tw-line-through')
                    discounted_price = discounted_price_element.text.strip() if discounted_price_element else 'N/A'

                    # Extract discount percentage
                    discount_element = product_element.find('span', class_='tw-font-bold', string=lambda text: 'OFF' in text)
                    discount = discount_element.text.strip() if discount_element else 'N/A'

                    # Extract image URL
                    image_element = product_element.find('img')
                    image_url = image_element['src'] if image_element else 'N/A'

                    # Open the product page to scrape color information
                    product_link = product_element.find('a')['href']
                    product_url = f"https://levi.in{product_link}"
                    driver.get(product_url)
                    color = scrape_color_info(driver)

                    # Insert the product details into the database
                    product_data = (name, price, discounted_price, discount, image_url, color)
                    insert_product_details(conn, product_data)

                print(f"[{datetime.datetime.now()}] Data inserted successfully")

        except sqlite3.Error as error:
            print('Error:', error)

        finally:
            if conn is not None:
                conn.close()
                print(f"[{datetime.datetime.now()}] SQLite connection closed")
            # Close the webdriver session
            driver.quit()

    except Exception as e:
        print('Error:', e)

# URL of the product listing page to scrape
url = 'https://levi.in/collections/men-shirts'

# Scrape product details from the listing page and store in SQLite database
scrape_product_details(url)
