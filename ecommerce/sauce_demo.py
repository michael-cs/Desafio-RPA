from botcity.web import By, WebBot
from framework.exceptions import BusinessException
from framework import config
import pandas as pd
import logging
import random
import csv

logger = logging.getLogger(__name__)

'''
sauce_demo.py
    Business logic for the Sauce Demo e-commerce (login, catalog scraping,
    random order selection, add-to-cart per item, and checkout).

    Selectors were re-collected in 2026-08 directly from the live site: it now
    exposes stable ids/data-test attributes/classes (#checkout, #continue,
    #finish, .inventory_item, .shopping_cart_link, etc.), so we select by
    those instead of the old absolute XPaths (/html/body/div/div[2]/...),
    which broke after the site's markup wrapper structure changed.
'''


def login(webbot: WebBot):
    webbot.browse(config.SAUCE_DEMO_URL)

    user_field = webbot.find_element("user-name", By.ID, ensure_visible=True)
    user_field.clear()
    user_field.send_keys(config.SAUCE_DEMO_USER)

    password_field = webbot.find_element("password", By.ID, ensure_visible=True)
    password_field.clear()
    password_field.send_keys(config.SAUCE_DEMO_PASSWORD)

    webbot.find_element("login-button", By.ID, ensure_clickable=True).click()
    logger.info("Logged into Sauce Demo.")


def scrape_catalog(webbot: WebBot):
    """
    Scrapes the 6 products listed on the Sauce Demo catalog page and writes
    them to assets/item_list.csv.
    """
    with open(config.CSV_ITEMS, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Item Number", "Item Name", "Description", "Price"])

        for i in range(1, 7):
            item_name = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_name",
                By.CSS_SELECTOR, ensure_visible=True
            ).text

            item_description = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_desc",
                By.CSS_SELECTOR, ensure_visible=True
            ).text

            item_price = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_price",
                By.CSS_SELECTOR, ensure_visible=True
            ).text.replace("$", "").replace(".", ",")

            logger.info(f"Scraped item {i}: {item_name} / {item_description} / {item_price}")
            writer.writerow([i, item_name, item_description, item_price])


def select_random_order(n: int = config.ORDER_SIZE) -> list:
    """
    Randomly picks `n` products from assets/item_list.csv, writes them to
    assets/order_list.csv and returns them as a list of dicts.
    """
    catalog = pd.read_csv(config.CSV_ITEMS)
    ordered_items = catalog.iloc[random.sample(range(len(catalog)), n)]

    with open(config.CSV_ORDER, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Item Number", "Item Name", "Description", "Price"])
        for _, row in ordered_items.iterrows():
            writer.writerow(row.tolist())

    logger.info(f"Order selected: {ordered_items['Item Name'].tolist()}")
    return ordered_items.to_dict("records")


def add_to_cart(webbot: WebBot, item: dict):
    """
    Adds the given order item (a row from order_list.csv) to the Sauce Demo cart.
    """
    i = int(item["Item Number"])
    add_button = webbot.find_element(
        f".inventory_item:nth-of-type({i}) button",
        By.CSS_SELECTOR, ensure_clickable=True
    )
    if add_button is None:
        raise BusinessException(
            f"Could not find the 'Add to cart' button for item {item.get('Item Name')}.",
            item_number=item.get("Item Number"), item_name=item.get("Item Name")
        )
    add_button.click()
    logger.info(f"Added to cart: {item.get('Item Name')}")


def checkout(webbot: WebBot, contact: dict):
    """
    Opens the cart, checks out using the fake buyer's data, and stores
    before/after screenshots of the purchase confirmation into ./output/
    as audit evidence.
    """
    webbot.find_element(
        ".shopping_cart_link", By.CSS_SELECTOR, ensure_clickable=True
    ).click()

    webbot.find_element(
        "checkout", By.ID, ensure_clickable=True
    ).click()

    first_name = webbot.find_element("first-name", By.ID, ensure_visible=True)
    first_name.clear()
    first_name.send_keys(contact["First Name"])

    last_name = webbot.find_element("last-name", By.ID, ensure_visible=True)
    last_name.clear()
    last_name.send_keys(contact["Last Name"])

    postal_code = webbot.find_element("postal-code", By.ID, ensure_visible=True)
    postal_code.clear()
    postal_code.send_keys(contact["Zip Code"])

    webbot.find_element(
        "continue", By.ID, ensure_clickable=True
    ).click()

    order_value = webbot.find_element(
        ".summary_total_label", By.CSS_SELECTOR, ensure_visible=True
    )
    webbot.driver.execute_script("arguments[0].scrollIntoView();", order_value)

    buyer = f"{contact['First Name']} {contact['Last Name']}"
    webbot.driver.get_screenshot_as_file(f"./output/sauce_demo_checkout_summary_{buyer}.png")

    webbot.find_element(
        "finish", By.ID, ensure_clickable=True
    ).click()

    webbot.driver.get_screenshot_as_file(f"./output/sauce_demo_checkout_complete_{buyer}.png")
    logger.info(f"Checkout completed for {buyer}.")
