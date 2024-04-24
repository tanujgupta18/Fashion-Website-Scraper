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

def scrape_color_info(driver):
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        color_element = soup.find('span', class_='tw-ml-[7px]')
        color = color_element.text.strip() if color_element else 'N/A'
        return color
    except Exception as e:
        print('Error scraping color information:', e)
        return 'N/A'

def scrape_product_details(url):
    scraped_data = []  
    try:
        driver = webdriver.Chrome()
        driver.maximize_window()
        driver.get(url)
        print(f"[{datetime.datetime.now()}] Webpage loaded.")

        wait = WebDriverWait(driver, 20)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))
        print(f"[{datetime.datetime.now()}] Dynamic content loaded.")

        last_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'product-card')))
            new_count = len(driver.find_elements(By.CLASS_NAME, 'product-card'))

            if new_count == last_count:
                break
            last_count = new_count

        print(f"[{datetime.datetime.now()}] All products loaded.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_elements = soup.find_all('div', class_='product-card')

        if not product_elements:
            product_elements = soup.find_all('div', class_='product-card__info')

        for product_element in product_elements:
            name_element = product_element.find('a', class_='product-card__title')
            name = name_element.text.strip() if name_element else 'N/A'

            price_element = product_element.find('span', class_='tw-font-bold')
            price = price_element.text.strip() if price_element else 'N/A'

            discounted_price_element = product_element.find('span', class_='tw-line-through')
            discounted_price = discounted_price_element.text.strip() if discounted_price_element else 'N/A'

            discount_element = product_element.find('span', class_='tw-font-bold', string=lambda text: 'OFF' in text)
            discount = discount_element.text.strip() if discount_element else 'N/A'

            image_element = product_element.find('img')
            image_url = image_element['src'] if image_element else 'N/A'

            product_link = product_element.find('a')['href']
            product_url = f"https://levi.in{product_link}"
            driver.get(product_url)
            color = scrape_color_info(driver)

            scraped_data.append({
                'name': name,
                'price': price,
                'discounted_price': discounted_price,
                'discount': discount,
                'image_url': image_url,
                'color': color
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

    return render(request, 'levis_scraper.html', {'form': form, 'scraped_data': scraped_data,
    'total_products': total_products})

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
