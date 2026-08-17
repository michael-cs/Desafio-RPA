from framework.logger import setup_botcity_log, setup_logger
from fakturama_desktop import desktop as fakturama_desktop
from botcity.web.browsers.firefox import default_options as firefox_default_options
from webdriver_manager.firefox import GeckoDriverManager
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
    (fake buyer + catalog scraping + Fakturama contact registration). Handles
    both initial startup and restart scenarios.

    On a SystemException restart, bootstrap() is intentionally NOT re-run: the
    fake buyer and the scraped catalog must stay exactly as they were,
    otherwise we'd overwrite assets/item_list.csv mid-iteration and create a
    duplicate Fakturama contact. Restart only reopens the browser and logs
    back into Sauce Demo.
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
    One-time setup that must run exactly once per execution: generates the
    fake buyer, scrapes the full Sauce Demo catalog, and registers the buyer
    as a Fakturama contact. The per-product Fakturama registration then runs
    as the item loop in bot.py (see framework/process.py::process_item()).
    """
    logger.info("Generating fake buyer contact...")
    STATE.contact = fake_contact.generate_contact(STATE.webbot)

    logger.info("Logging into Sauce Demo and scraping the catalog...")
    sauce_demo.login(STATE.webbot)
    sauce_demo.scrape_catalog(STATE.webbot)

    logger.info("Registering the buyer as a Fakturama contact...")
    fakturama_desktop.ensure_running(STATE.desktopbot)
    fakturama_desktop.register_contact(STATE.desktopbot, STATE.contact)

    datasources.data_source = datasources.CSVSource(config.CSV_ITEMS)


def init_webbot():
    """Instantiates BotCity's WebBot using Firefox and opens the browser."""
    STATE.webbot = WebBot()
    bot = STATE.webbot
    bot.browser = Browser.FIREFOX
    bot.headless = False
    # Unlike undetected-chromedriver, geckodriver isn't self-managed - WebBot
    # needs a real driver executable here. webdriver-manager downloads/caches
    # the matching geckodriver for the installed Firefox version and returns
    # its path.
    bot.driver_path = GeckoDriverManager().install()

    # Without this, Firefox defaults its download folder to the current
    # working directory (the project root) - stray downloads end up
    # committed-looking next to the source files.
    download_folder = str(Path(__file__).parent.parent / "temp")
    bot.options = firefox_default_options(headless=bot.headless, download_folder_path=download_folder)

    bot.start_browser()


def init_desktopbot():
    """Instantiates BotCity's DesktopBot and registers the Fakturama UI images."""
    STATE.desktopbot = DesktopBot()
    fakturama_desktop.register_images(STATE.desktopbot)


def setup_temp_folders():
    shutil.rmtree("./output", ignore_errors=True)
    Path("./output").mkdir(parents=True, exist_ok=True)
    shutil.rmtree("./temp", ignore_errors=True)
    Path("./temp").mkdir(parents=True, exist_ok=True)
