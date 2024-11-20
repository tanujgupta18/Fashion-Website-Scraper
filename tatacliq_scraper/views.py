from django.shortcuts import render
from .forms import ScrapeForm
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import datetime
import traceback

def scroll_page_slowly(driver, scroll_pause_time=1.0, scroll_increment=300, max_scrolls=10):
    """Function to scroll the page gradually to load images dynamically."""
    # Get the current scroll height of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    for _ in range(max_scrolls):
        driver.execute_script(f"window.scrollBy(0, {scroll_increment});")  # Scroll down by a fixed increment
        time.sleep(scroll_pause_time)  # Wait for content to load
        
        # Get the new scroll height and check if we've reached the bottom of the page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:  # If we've reached the bottom, break the loop
            break
        last_height = new_height

def scrape_product_details(url):
    scraped_data = []
    try:
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.get(url)
        print(f"[{datetime.datetime.now()}] Webpage loaded.")

        # Scroll the page slowly to load dynamic content like images
        scroll_page_slowly(driver, scroll_pause_time=2, scroll_increment=300, max_scrolls=10)

        wait = WebDriverWait(driver, 10)
        product_containers = wait.until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "ProductModule__imageAndDescriptionWrapper")))
        print(f"[{datetime.datetime.now()}] Dynamic content loaded.")

        for container in product_containers:
            try:
                brand_name = container.find_element(By.CLASS_NAME, 'ProductDescription__headerText').find_element(By.CLASS_NAME, 'ProductDescription__boldText').text.strip()
            except NoSuchElementException:
                brand_name = "Brand name not available"

            try:
                product_name = container.find_element(By.CLASS_NAME, 'ProductDescription__description').text.strip()
            except NoSuchElementException:
                product_name = "Product name not available"

            try:
                current_price = container.find_element(By.XPATH, './/div[@class="ProductDescription__content"]//h3').text.strip()
            except NoSuchElementException:
                current_price = "Price not available"

            try:
                original_price = container.find_element(By.XPATH, './/div[@class="ProductDescription__priceCancelled ProductDescription__priceHolder"]/span').text.strip()
            except NoSuchElementException:
                original_price = current_price

            try:
                discount = container.find_element(By.CLASS_NAME, 'ProductDescription__newDiscountPercent').text.strip()
            except NoSuchElementException:
                discount = "Discount not available"

            try:
                wait.until(EC.visibility_of(container.find_element(By.CLASS_NAME, 'Image__actual')))
                image_url = container.find_element(By.CLASS_NAME, 'Image__actual').get_attribute('src')
            except (NoSuchElementException, TimeoutException):
                image_url = "Image not available"
                
            try:
                product_url = container.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except NoSuchElementException:
                product_url = "URL not available"

            scraped_data.append({
                'brand_name': brand_name,
                'product_name': product_name,
                'current_price': current_price,
                'original_price': original_price,
                'discount': discount,
                'image_url': image_url,
                'product_url': product_url
            })

        return scraped_data

    except Exception as e:
        print('Error:', e)
        traceback.print_exc()
    finally:
        driver.quit()

def index(request):
    scraped_data = request.session.get('scraped_data', None)
    total_products = len(scraped_data) if scraped_data else 0  
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                scraped_data = scrape_product_details(url)
                request.session['scraped_data'] = scraped_data
                form = ScrapeForm()
    else:
        form = ScrapeForm()

    return render(request, 'tatacliq_scraper.html', {'form': form, 'scraped_data': scraped_data, 'total_products': total_products})

def scrape_and_store(request):
    scraped_data = request.session.get('scraped_data', None)
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                scraped_data = scrape_product_details(url)
                request.session['scraped_data'] = scraped_data
    else:
        form = ScrapeForm()

    return render(request, 'tatacliq_scraper.html', {'form': form, 'scraped_data': scraped_data})
