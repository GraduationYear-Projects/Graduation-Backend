from bs4 import BeautifulSoup
import json

# Read the HTML file
with open("Amazon.eg.html", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "html.parser")

# Find all product divs
product_divs = soup.find_all("div", class_="sg-col-4-of-24 sg-col-4-of-12 s-result-item s-asin sg-col-4-of-16 sg-col s-widget-spacing-small sg-col-4-of-20")

products = []
for div in product_divs:
    # Extract product image URL
    try:
        img_tag = div.find("img", class_="s-image")
        link = img_tag["src"] if img_tag else ""
    except:
        link = ""
    
    # Extract product title
    try:
        title_span = div.find("h2").find("span")
        title = title_span.text.strip() if title_span else ""
    except:
        title = ""
    
    # Extract product rating
    try:
        rating_span = div.find("span", class_="a-icon-alt")
        rating = rating_span.text.strip() if rating_span else ""
    except:
        rating = ""
    
    # Extract product price
    try:
        price_span = div.find("span", class_="a-price-whole")
        price = price_span.text.strip() if price_span else ""
    except:
        price = ""
    
    products.append({
        "link": link,
        "title": title,
        "rating": rating,
        "price": price
    })

# Write data to JSON file
with open("data.json", "w", encoding="utf-8") as json_file:
    json.dump(products, json_file, indent=4, ensure_ascii=False)

print("Data extracted and saved to data.json")
