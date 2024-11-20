from django.shortcuts import render
from .forms import ScrapeForm
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time
import datetime
import traceback

# Scrape color information
def scrape_color_info(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        color_element = soup.find('p', class_='product-card__color')
        color = color_element.text.strip() if color_element else 'N/A'
        return color
    except Exception as e:
        print('Error scraping color information:', e)
        return 'N/A'

# Scrape product details from the page
def scrape_product_details(url):
    scraped_data = []
    try:
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.get(url)
        print(f"[{datetime.datetime.now()}] Webpage loaded.")

        # Wait until products are loaded on the page
        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))
        print(f"[{datetime.datetime.now()}] Dynamic content loaded.")

        # Scroll to load all products dynamically
        last_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Ensure the page has enough time to load more products

            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))
            new_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))

            if new_count == last_count:
                break
            last_count = new_count

        print(f"[{datetime.datetime.now()}] All products loaded.")

        # Parse the page using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_elements = soup.find_all('div', class_='product-card')

        for product_element in product_elements:
            # Extracting product name
            name_element = product_element.find('a', class_='product-card__title')
            name = name_element.text.strip() if name_element else 'N/A'

            # Extracting price
            price_element = product_element.find('p', class_='tw-font-secondary')
            price = price_element.text.strip() if price_element else 'N/A'

            # Extracting discounted price
            discounted_price_element = product_element.find('p', class_='tw-line-through')
            discounted_price = discounted_price_element.text.strip() if discounted_price_element else 'N/A'

            # Extracting discount
            discount_element = product_element.find('p', class_='tw-px-[2px] tw-py-[1px] tw-rounded tw-text-[10px] lg:tw-text-[11px] tw-leading-none tw-font-primary tw-text-[#089657] tw-font-bold')
            discount = discount_element.text.strip() if discount_element else 'N/A'

            # Extracting image URL
            image_element = product_element.find('img', class_='image')
            image_url = image_element['src'] if image_element else 'N/A'

            # Scrape the product URL from the image link
            product_link = product_element.find('a', class_='media media--portrait product-card-image')['href']
            product_url = f"https://levi.in{product_link}"

            # Scrape color info for this specific product (optional, depending on data availability)
            color = scrape_color_info(driver)

            # Store the scraped product info
            scraped_data.append({
                'name': name,
                'price': price,
                'discounted_price': discounted_price,
                'discount': discount,
                'image_url': image_url,
                'product_url': product_url,
                'color': color
            })

        return scraped_data

    except Exception as e:
        print('Error scraping product details:', e)
        traceback.print_exc()
    finally:
        driver.quit()

# View for handling the scraping process
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
                form = ScrapeForm()  # Reset the form after submission
    else:
        form = ScrapeForm()

    return render(request, 'levis_scraper.html', {
        'form': form, 
        'scraped_data': scraped_data,
        'total_products': total_products
    })

# Scrape and store view for background processing
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

    return render(request, 'levis_scraper.html', {'form': form, 'scraped_data': scraped_data})
