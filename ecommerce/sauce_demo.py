from framework.state import STATE
from botcity.web import By, WebBot
from framework.exceptions import SystemException
from framework import config
import logging
import win32gui
import time
import csv

logger = logging.getLogger(__name__)

'''
sauce_demo.py
    Business logic for the Sauce Demo e-commerce: login and full catalog
    scraping. This is the "web automation" half of the class exercise -
    the "desktop automation" half (fakturama_desktop/desktop.py) replicates
    the same buyer/catalog data into Fakturama.

    Selectors were re-collected in 2026-08 directly from the live site: it now
    exposes stable ids/data-test attributes/classes (.inventory_item, etc.),
    so we select by those instead of the old absolute XPaths
    (/html/body/div/div[2]/...), which broke after the site's markup wrapper
    structure changed.
'''


def _focus_browser_window():
    """
    The browser window doesn't reliably receive OS-level foreground focus
    (Windows blocks SetForegroundWindow from processes with no recent real
    input, e.g. when the bot is launched from a script/service rather than
    typed interactively into a terminal). Without OS focus, Selenium's
    send_keys() silently no-ops - clicks and .text reads still work fine,
    only keyboard input needs this. A real OS-level mouse click (not the
    SetForegroundWindow API, which is exactly what gets blocked) reliably
    fixes it, so we do that before every send_keys() call in this module.
    Matches on "Swag Labs" (the page title), which Firefox/Chrome both show
    in the window title regardless of which browser is configured.
    """
    windows = []
    win32gui.EnumWindows(
        lambda hwnd, acc: acc.append(hwnd)
        if win32gui.IsWindowVisible(hwnd) and "Swag Labs" in win32gui.GetWindowText(hwnd)
        else None,
        windows,
    )
    if not windows:
        return
    left, top, right, _ = win32gui.GetWindowRect(windows[0])
    STATE.desktopbot.click_at((left + right) // 2, top + 80)


def login(webbot: WebBot):
    webbot.browse(config.SAUCE_DEMO_URL)
    _focus_browser_window()

    user_field = webbot.find_element("user-name", By.ID, ensure_visible=True)
    user_field.clear()
    user_field.send_keys(config.SAUCE_DEMO_USER)

    password_field = webbot.find_element("password", By.ID, ensure_visible=True)
    password_field.clear()
    password_field.send_keys(config.SAUCE_DEMO_PASSWORD)

    webbot.find_element("login-button", By.ID, ensure_clickable=True).click()

    # Each run uses a fresh browser profile (no cache), so the client-side
    # transition to the catalog page varies in speed between runs.
    # Wait for it here so scrape_catalog() always starts from a ready page,
    # instead of racing the first item's find_element against a slow load.
    webbot.find_element(".inventory_list", By.CSS_SELECTOR, ensure_visible=True, waiting_time=20000)
    logger.info("Logged into Sauce Demo.")


def _wait_for_catalog_items(webbot: WebBot, expected_count: int = 6, timeout: int = 60, refresh_after: int = 15):
    """
    Waits for the catalog to actually render its products. This is a
    client-rendered SPA with a fresh (uncached) profile on every run, and it
    occasionally leaves .inventory_list empty on the first load with no
    visible error - a page refresh reliably gets it to re-fetch and render,
    so we refresh periodically instead of just re-querying the same page.
    """
    deadline = time.monotonic() + timeout
    next_refresh = time.monotonic() + refresh_after
    while time.monotonic() < deadline:
        count = webbot.driver.execute_script("return document.querySelectorAll('.inventory_item').length;")
        if count >= expected_count:
            return
        if time.monotonic() >= next_refresh:
            logger.info(f"Catalog has {count}/{expected_count} items rendered, refreshing the page...")
            webbot.driver.refresh()
            next_refresh = time.monotonic() + refresh_after
        time.sleep(1)

    # Diagnostics for whatever's actually happening, captured at the moment
    # of failure instead of needing a live repro afterwards.
    try:
        console_logs = webbot.driver.get_log("browser")
        logger.error(f"Browser console at time of failure: {console_logs}")
    except Exception as ex:
        logger.error(f"Could not read browser console logs: {ex}")
    webbot.driver.get_screenshot_as_file("./temp/catalog_load_failure.png")
    raise SystemException("A página do catálogo não terminou de carregar os produtos a tempo.")


def scrape_catalog(webbot: WebBot):
    """
    Scrapes the 6 products listed on the Sauce Demo catalog page and writes
    them to assets/item_list.csv.
    """
    _wait_for_catalog_items(webbot)

    with open(config.CSV_ITEMS, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Item Number", "Item Name", "Description", "Price"])

        for i in range(1, 7):
            item_name = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_name", By.CSS_SELECTOR, ensure_visible=True
            ).text
            item_description = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_desc", By.CSS_SELECTOR, ensure_visible=True
            ).text
            item_price = webbot.find_element(
                f".inventory_item:nth-of-type({i}) .inventory_item_price", By.CSS_SELECTOR, ensure_visible=True
            ).text.replace("$", "").replace(".", ",")

            logger.info(f"Scraped item {i}: {item_name} / {item_description} / {item_price}")
            writer.writerow([i, item_name, item_description, item_price])
