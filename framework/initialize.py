from framework.logger import setup_botcity_log, setup_logger
from fakturama_desktop import desktop as fakturama_desktop
from botcity.web import Browser, WebBot
from framework.finalize import cleanup
from ecommerce import fake_contact, sauce_demo
from botcity.core import DesktopBot
from framework.state import STATE
from framework import config, datasources
from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)

'''
initialize.py
    Starts the automation process by setting up the logger, cleaning the output
    directory, opening the browser/Fakturama, and running the one-time bootstrap
    (fake buyer, catalog scraping, random order pick, Fakturama contact/catalog/
    order setup). Handles both initial startup and restart scenarios.

    On a SystemException restart, bootstrap() is intentionally NOT re-run: the
    fake buyer, the scraped catalog, the randomly picked order and the already
    open Fakturama order must stay exactly as they were, otherwise we'd overwrite
    assets/order_list.csv mid-iteration and create duplicate Fakturama records.
    Restart only reopens the browser and logs back into Sauce Demo.
'''


def run_once():
    try:
        setup_temp_folders()
        setup_logger()
        setup_botcity_log()
        execution = STATE.execution
        logger.info(
            f"Automation {STATE.task_info().activity_name} started. Task ID: {execution.task_id}")
        print(f"Task ID: {execution.task_id}")
        if execution.parameters:
            print(f"Task Parameters are: {execution.parameters}")
    except Exception as ex:
        raise ex


def initialize(restart: bool = False):
    try:
        STATE.raise_for_interrupt_requested()
        if restart:
            logger.info("Recovering from exception to continue processing remaining items...")
            cleanup()
            init_webbot()
            sauce_demo.login(STATE.webbot)
        else:
            run_once()
            init_webbot()
            init_desktopbot()
            bootstrap()
    except Exception as ex:
        raise ex


def bootstrap():
    """
    One-time setup that must run exactly once per execution: generates the fake
    buyer, scrapes the Sauce Demo catalog, randomly picks the order, and
    registers the buyer/catalog/new-order in Fakturama.
    """
    logger.info("Generating fake buyer contact...")
    STATE.contact = fake_contact.generate_contact(STATE.webbot)

    logger.info("Logging into Sauce Demo and scraping the catalog...")
    sauce_demo.login(STATE.webbot)
    sauce_demo.scrape_catalog(STATE.webbot)

    logger.info(f"Selecting {config.ORDER_SIZE} random products to purchase...")
    sauce_demo.select_random_order()

    logger.info("Registering buyer and full catalog in Fakturama...")
    fakturama_desktop.ensure_running(STATE.desktopbot)
    fakturama_desktop.register_contact(STATE.desktopbot, STATE.contact)
    fakturama_desktop.register_all_products(STATE.desktopbot)
    fakturama_desktop.open_new_order(STATE.desktopbot, STATE.contact)

    datasources.data_source = datasources.CSVSource(config.CSV_ORDER)


def init_webbot():
    """Instantiates BotCity's WebBot using undetected-chromedriver and opens the browser."""
    STATE.webbot = WebBot()
    bot = STATE.webbot
    bot.browser = Browser.UNDETECTED_CHROME
    bot.headless = False


def init_desktopbot():
    """Instantiates BotCity's DesktopBot and registers the Fakturama UI images."""
    STATE.desktopbot = DesktopBot()
    fakturama_desktop.register_images(STATE.desktopbot)


def setup_temp_folders():
    shutil.rmtree("./output", ignore_errors=True)
    Path("./output").mkdir(parents=True, exist_ok=True)
    shutil.rmtree("./temp", ignore_errors=True)
    Path("./temp").mkdir(parents=True, exist_ok=True)
