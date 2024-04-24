from django.shortcuts import render
from .forms import ScrapeForm
import requests
from bs4 import BeautifulSoup

def scrape_products(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    num_products = 0
    page = 1
    scraped_data = []

    while num_products < 200:
        response = requests.get(url.format(page), headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            product_containers = soup.find_all('div', class_='evejxsf1 css-384pms')

            if not product_containers:
                break

            for container in product_containers:
                product_name = container.find('div', {'data-at': 'product-title'}).text.strip()
                product_subtitle = container.find('div', {'data-at': 'product-subtitle'}).text.strip()
                current_price = container.select_one('.css-fri5as').text.strip().split('₹')[1]
                current_price = "₹ " + current_price
                original_price_element = container.select_one('.css-1vhnk55')
                original_price = "₹ " + original_price_element.text.strip().split('₹')[1] if original_price_element else "N/A"
                discount_element = container.select_one('.css-q6csrj')
                discount = discount_element.text.strip() if discount_element else "N/A"
                image_url = container.find('img', {'data-at': 'product-img'})['src']

                scraped_data.append({
                    'product_name': product_name,
                    'product_subtitle': product_subtitle,
                    'current_price': current_price,
                    'original_price': original_price,
                    'discount': discount,
                    'image_url': image_url
                })

                num_products += 1

            print(f"Scraped {num_products} products so far.")

            page += 1
        else:
            print("Failed to retrieve page.")
            break

    print("Scraping completed.")
    return scraped_data

def index(request):
    scraped_data = request.session.get('scraped_data', None)
    total_products = len(scraped_data) if scraped_data else 0
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                scraped_data = scrape_products(url)
                request.session['scraped_data'] = scraped_data
    else:
        form = ScrapeForm()

    return render(request, 'nyka_scraper.html', {'form': form, 'scraped_data': scraped_data, 'total_products': total_products})

def scrape_and_store(request):
    scraped_data = request.session.get('scraped_data', None)
    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                scraped_data = scrape_products(url)
                request.session['scraped_data'] = scraped_data
    else:
        form = ScrapeForm()

    return render(request, 'nyka_scraper.html', {'form': form, 'scraped_data': scraped_data})