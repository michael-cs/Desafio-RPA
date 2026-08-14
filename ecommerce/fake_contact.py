from botcity.web import By, WebBot
from framework import config
import logging
import csv

logger = logging.getLogger(__name__)

'''
fake_contact.py
    Generates a fake Brazilian buyer (name + CEP) from fakenamegenerator.com.
    This buyer is used both as the Sauce Demo checkout contact and as the
    contact registered in Fakturama, so the two purchases can be compared.
'''


def generate_contact(webbot: WebBot) -> dict:
    """
    Scrapes a random contact from fakenamegenerator.com and writes it to
    assets/contact_list.csv.
    Returns: dict with First Name, Last Name and Zip Code.
    """
    webbot.browse(config.FAKE_NAME_GENERATOR_URL)

    full_name = webbot.find_element(
        '//div[@class="address"]/h3[1]', By.XPATH, ensure_visible=True
    ).text.split()
    first_name = full_name[0]
    last_name = full_name[-1]

    address_lines = webbot.find_element(
        '//div[@class="adr"]', By.XPATH, ensure_visible=True
    ).text.splitlines()
    zip_code = address_lines[2]

    contact = {"First Name": first_name, "Last Name": last_name, "Zip Code": zip_code}
    logger.info(f"Generated fake contact: {contact}")

    with open(config.CSV_CONTACT, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(contact.keys()))
        writer.writeheader()
        writer.writerow(contact)

    return contact
