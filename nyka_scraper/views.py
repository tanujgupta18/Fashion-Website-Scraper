from django.shortcuts import render
from .forms import ScrapeForm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def scrape_products(url):
    options = Options()
    options.headless = True  # Run browser in headless mode (without UI)
    
    # Automatically download and manage chromedriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(5)  # Wait for JavaScript to load and render the page
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    scraped_data = []
    num_products = 0

    # Adjust the container class to match Nykaa's product container
    product_containers = soup.find_all('div', class_='evejxsf1 css-384pms')

    if not product_containers:
        print("No product containers found on the page.")
    
    for container in product_containers:
        try:
            product_name = container.find('div', {'data-at': 'product-title'}).text.strip()
            product_subtitle = container.find('div', {'data-at': 'product-subtitle'}).text.strip()
            current_price = container.select_one('.css-fri5as').text.strip().split('₹')[1]
            current_price = "₹ " + current_price

            original_price_element = container.select_one('.css-1vhnk55')
            original_price = "₹ " + original_price_element.text.strip().split('₹')[1] if original_price_element else "N/A"

            discount_element = container.select_one('.css-q6csrj')
            discount = discount_element.text.strip() if discount_element else "N/A"

            image_url = container.find('img', {'data-at': 'product-img'})['src']

            # Append the data to the list
            scraped_data.append({
                'product_name': product_name,
                'product_subtitle': product_subtitle,
                'current_price': current_price,
                'original_price': original_price,
                'discount': discount,
                'image_url': image_url
            })
            num_products += 1
        except Exception as e:
            print(f"Error extracting product details: {e}")


    driver.quit()  # Close the browser
    return scraped_data

# View to handle user input, scrape data, and render the results
def index(request):
    # Retrieve scraped data from session if it exists
    scraped_data = request.session.get('scraped_data', [])
    
    total_products = len(scraped_data)  # Get the total number of products

    if request.method == 'POST':
        form = ScrapeForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if url:
                # Scrape the products using the URL entered by the user
                scraped_data = scrape_products(url)
                # Store the scraped data in the session
                request.session['scraped_data'] = scraped_data
    else:
        form = ScrapeForm()

    return render(request, 'nyka_scraper.html', {
        'form': form,
        'scraped_data': scraped_data,
        'total_products': total_products
    })
