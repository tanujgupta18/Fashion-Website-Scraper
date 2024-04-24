from django.shortcuts import render
from .forms import ScrapeForm
import requests
from bs4 import BeautifulSoup
import re

def format_price(price):
    price = re.sub(r'[^\d.]', '', price)
    formatted_price = "{:.2f}".format(float(price))
    formatted_price = "₹" + str(int(float(formatted_price)))
    return formatted_price

def scrape_pepejeans_products(url):
    scraped_products = []

    page_number = 1
    while len(scraped_products) < 200:  
        page_url = f"{url}?page={page_number}"
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error accessing URL: {e}")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = soup.find_all('div', class_='product-item')

        if not products:
            break

        for product in products:
            product_data = {}

            product_name_tag = product.find('a', class_='link')
            if product_name_tag:
                product_data['name'] = product_name_tag.get_text(strip=True)
            else:
                continue

            original_price_tag = product.find('span', class_='strike-through list')
            if original_price_tag:
                original_price = original_price_tag.find('span', class_='value').get('content')
                product_data['original_price'] = format_price(original_price)
            else:
                product_data['original_price'] = None

            current_price_tag = product.find('span', class_='sales discount-sales')
            if current_price_tag:
                current_price = current_price_tag.find('span', class_='value').get('content')
                product_data['current_price'] = format_price(current_price)
            else:
                continue

            discount_percentage_tag = product.find('div', class_='discount-percentage')
            if discount_percentage_tag:
                discount_percentage = discount_percentage_tag.get_text(strip=True).replace('(', '').replace(')', '')
                product_data['discount_percentage'] = discount_percentage
            else:
                product_data['discount_percentage'] = None

            product_image_url = product.find('img', class_='tile-image')['data-src']
            product_data['image_url'] = product_image_url

            product_url = product.find('a', class_='link')['href']
            product_data['url'] = f"https://www.pepejeans.in{product_url}"

            try:
                product_response = requests.get(product_data['url'], timeout=10)  
                product_response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error accessing product URL: {e}")
                continue

            product_soup = BeautifulSoup(product_response.content, 'html.parser')

            color_options = product_soup.find('div', class_='attribute-color')
            if color_options:
                colors = color_options.find_all('span', class_='color-value')
                color_list = [color.get('data-attr-value') for color in colors]
                product_data['colors'] = color_list
            else:
                product_data['colors'] = None

            scraped_products.append(product_data)

            if len(scraped_products) >= 200:
                break

        page_number += 1

    return scraped_products

def index(request):
    scraped_data = None
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                scraped_data = scrape_pepejeans_products(url)
    else:
        form = ScrapeForm()

    return render(request, 'pepejeans_scraper.html', {'form': form, 'scraped_data': scraped_data})
