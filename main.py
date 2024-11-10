import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import pandas as pd

SLEEP_TIME = 0.5


def initializes_driver():
    """Initializes driver with maximized option"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def get_travel_and_nonfiction_category_urls(driver, url):
    """Gets category URLs from given homepage url"""
    driver.get(url)
    time.sleep(SLEEP_TIME)
    category_elements_xpath = "//a[contains(text(),'Travel') or contains(text(), 'Nonfiction')]"
    category_elements = driver.find_elements(By.XPATH, category_elements_xpath)
    category_urls = [element.get_attribute("href") for element in category_elements]
    return category_urls


def get_book_urls(driver, url):
    """Gets book urls from given category detail page url"""
    MAX_PAGINATION = 4
    book_urls = []
    book_elements_xpath = "//div[@class='image_container']//a"

    for i in range(1, MAX_PAGINATION):
        updated_url = url if i == 1 else url.replace("index", f"page-{i}")
        driver.get(updated_url)
        time.sleep(SLEEP_TIME)
        book_elements = driver.find_elements(By.XPATH, book_elements_xpath)

        # Controller of pagination
        if not book_elements:
            break
        temp_urls = [element.get_attribute("href") for element in book_elements]
        book_urls.extend(temp_urls)

    return book_urls


def get_book_detail(driver, url):
    """Gets book data from given book detail page url"""
    driver.get(url)
    time.sleep(SLEEP_TIME)
    content_div = driver.find_elements(By.XPATH, "//div[@class='content']")
    inner_html = content_div[0].get_attribute("innerHTML")

    soup = BeautifulSoup(inner_html, "html.parser")

    # Get book details
    name_elem = soup.find("h1")
    book_name = name_elem.text if name_elem else 'N/A'

    price_elem = soup.find("p", attrs={"class": "price_color"})
    book_price = price_elem.text if price_elem else 'N/A'

    regex = re.compile('^star-rating ')
    star_elem = soup.find("p", attrs={"class": regex})
    book_star_count = star_elem["class"][-1] if star_elem else 'N/A'

    desc_elem = soup.find("div", attrs={"id": "product_description"})
    book_desc = desc_elem.find_next_sibling().text if desc_elem else 'N/A'

    # Get product info table
    product_info = {}
    table_rows = soup.find("table").find_all("tr")
    for row in table_rows:
        key = row.find("th").text
        value = row.find("td").text
        product_info[key] = value

    return {
        'book_name': book_name,
        'book_price': book_price,
        'book_star_count': book_star_count,
        'book_desc': book_desc,
        **product_info
    }


def main():
    BASE_URL = "https://books.toscrape.com/"
    driver = initializes_driver()
    category_urls = get_travel_and_nonfiction_category_urls(driver, BASE_URL)
    data = []

    for cat_url in category_urls:
        book_urls = get_book_urls(driver, cat_url)
        for book_url in book_urls:
            book_data = get_book_detail(driver, book_url)
            book_data["cat_url"] = cat_url
            data.append(book_data)

    # Convert to DataFrame and display
    df = pd.DataFrame(data)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.max_width", None)

    return df


# Run the main function
df = main()
print(df.head())
print(df.shape)
