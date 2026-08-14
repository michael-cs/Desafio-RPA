from framework.exceptions import SystemException, BusinessException
from botcity.core import DesktopBot
from framework import config
import pandas as pd
import logging

logger = logging.getLogger(__name__)

'''
desktop.py
    Business logic for the Fakturama desktop app: registering the buyer,
    registering the full product catalog, opening a new order and typing
    each ordered product line into it, then saving/exporting the order.

    Image matching (DesktopBot.find) replaces the old pyautogui.locateOnScreen
    retry loop; DesktopBot already retries internally until `waiting_time`.
'''

IMAGES = {
    "products_db": "label_products.PNG",
    "search_products_db": "field_search_product.PNG",
    "listed_item": "label_item_number.PNG",
    "new_product": "btn_new_product.PNG",
    "label_new_product": "label_new_product.PNG",
    "new_contact": "btn_new_contact.PNG",
    "new_order": "btn_new_order.PNG",
    "contact_list": "btn_contact_list.PNG",
    "first_item": "btn_first_item.PNG",
    "product_list": "btn_product_list.PNG",
}


def register_images(desktop: DesktopBot):
    """Registers every Fakturama UI image used for matching. Call once during initialize()."""
    for label, filename in IMAGES.items():
        desktop.add_image(label, config.IMAGES_FOLDER + filename)


def _find_or_raise(desktop: DesktopBot, label: str, **kwargs):
    element = desktop.find(label, matching=0.7, grayscale=True, **kwargs)
    if element is None:
        raise SystemException(f'Imagem "{label}" não localizada na tela.')
    return element


def ensure_running(desktop: DesktopBot):
    """Starts Fakturama if it isn't already running."""
    if desktop.find_process(name=config.FAKTURAMA_PROCESS_NAME) is None:
        desktop.execute(config.FAKTURAMA_EXE_PATH)


def _validate_product(desktop: DesktopBot, item_name: str):
    """Searches the given product in the Fakturama product database and clears the search field."""
    _find_or_raise(desktop, "products_db")
    desktop.click()

    _find_or_raise(desktop, "search_products_db")
    desktop.click()
    desktop.click_relative(100, 0)
    desktop.kb_type(item_name)

    _find_or_raise(desktop, "listed_item")
    desktop.click()
    desktop.click_relative(0, 15)

    _find_or_raise(desktop, "search_products_db")
    desktop.click()
    desktop.click_relative(160, 0)
    desktop.control_key("d")
    desktop.enter()


def register_all_products(desktop: DesktopBot):
    """Registers the full Sauce Demo catalog (assets/item_list.csv) in Fakturama."""
    ensure_running(desktop)
    catalog = pd.read_csv(config.CSV_ITEMS)

    _find_or_raise(desktop, "new_product", waiting_time=30000)

    for _, row in catalog.iterrows():
        item_number = str(row["Item Number"])
        item_name = row["Item Name"]
        description = row["Description"]
        price = str(row["Price"])

        _validate_product(desktop, item_name)

        _find_or_raise(desktop, "new_product")
        desktop.click()
        _find_or_raise(desktop, "label_new_product")
        desktop.click()

        desktop.tab(presses=2)
        desktop.kb_type(item_number)
        logger.info(item_number)
        desktop.tab(presses=1)
        desktop.kb_type(item_name)
        logger.info(item_name)
        desktop.tab(presses=1)
        desktop.kb_type("Shop")
        desktop.tab(presses=3)
        desktop.kb_type(description)
        logger.info(description)
        desktop.tab(presses=1)
        desktop.kb_type(price)
        desktop.control_s()
        desktop.control_w()


def register_contact(desktop: DesktopBot, contact: dict):
    """Registers the fake buyer as a new Fakturama contact."""
    ensure_running(desktop)
    _find_or_raise(desktop, "new_contact", waiting_time=30000)
    desktop.click()

    desktop.tab(presses=4)
    desktop.paste(contact["First Name"])
    desktop.tab(presses=1)
    desktop.paste(contact["Last Name"])
    desktop.tab(presses=8)
    desktop.kb_type(contact["Zip Code"])
    desktop.control_s()
    desktop.control_w()


def open_new_order(desktop: DesktopBot, contact: dict):
    """Opens a new Fakturama order, selects the buyer's contact, and leaves the
    first product row ready to be filled in by add_order_line()."""
    ensure_running(desktop)
    _find_or_raise(desktop, "new_order", waiting_time=30000)
    desktop.click()

    _find_or_raise(desktop, "contact_list")
    desktop.click()
    desktop.paste(contact["First Name"])

    _find_or_raise(desktop, "first_item")
    desktop.click()
    desktop.double_click_relative(40, 0)


def add_order_line(desktop: DesktopBot, item: dict):
    """Types one ordered product into the currently open Fakturama order."""
    element = desktop.find("product_list", matching=0.7, grayscale=True)
    if element is None:
        raise BusinessException(
            f"Could not find the product list field for {item.get('Item Name')}.",
            item_number=item.get("Item Number"), item_name=item.get("Item Name")
        )
    desktop.click()
    desktop.kb_type(item["Item Name"], interval=100)


def finish_order(desktop: DesktopBot):
    """Saves the order, exports it to PDF (default PDF printer) and closes Fakturama."""
    desktop.control_s()
    desktop.control_p()
    desktop.control_w()

    process = desktop.find_process(name=config.FAKTURAMA_PROCESS_NAME)
    if process:
        desktop.terminate_process(process)
