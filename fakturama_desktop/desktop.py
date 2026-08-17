from framework.exceptions import SystemException
from botcity.core import DesktopBot
from framework import config
import win32process
import win32gui
import win32con
import logging
import time

logger = logging.getLogger(__name__)

'''
desktop.py
    Business logic for the Fakturama desktop app: registering the fake buyer
    as a contact and each scraped Sauce Demo product as a new item. This is
    the "desktop automation" half of the class exercise - image matching
    (DesktopBot.find) replaces the old pyautogui.locateOnScreen retry loop,
    DesktopBot already retries internally until `waiting_time`.
'''

IMAGES = {
    "new_product": "btn_new_product.PNG",
    "label_new_product": "label_new_product.PNG",
    "new_contact": "btn_new_contact.PNG",
    "products_db": "label_products.PNG",
}


def register_images(desktop: DesktopBot):
    """Registers every Fakturama UI image used for matching. Call once during initialize()."""
    for label, filename in IMAGES.items():
        desktop.add_image(label, config.IMAGES_FOLDER + filename)


def _find_or_raise(desktop: DesktopBot, label: str, **kwargs):
    element = desktop.find(label, matching=0.7, grayscale=True, **kwargs)
    if element is None:
        try:
            desktop.save_screenshot(f"./temp/fakturama_not_found_{label}.png")
        except Exception:
            pass
        raise SystemException(f'Imagem "{label}" não localizada na tela.')
    return element


def _focus_window_by_pid(desktop: DesktopBot, pid: int):
    """
    Real OS-level click to bring Fakturama's window to the foreground before
    any image search/typing. We alternate between the browser and Fakturama
    throughout the run, and each one grabbing focus for its own typing leaves
    the other covered/behind - image search only looks at the visible screen,
    so it fails to find anything if Fakturama isn't the frontmost window.
    """
    windows = []

    def _collect(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid:
                windows.append(hwnd)

    win32gui.EnumWindows(_collect, None)
    if not windows:
        return
    hwnd = windows[0]

    # DesktopBot only captures/searches the primary monitor (its display_size()).
    # If Fakturama's window is sitting on a secondary monitor - e.g. because it
    # remembered its last position from a previous session - every image
    # search on it silently finds nothing, even though it's focused and
    # perfectly visible to a human. Move it back onto the primary monitor.
    primary_width, _ = desktop.display_size()
    left, top, right, _ = win32gui.GetWindowRect(hwnd)
    if left >= primary_width:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.MoveWindow(hwnd, 50, 50, 1200, 800, True)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        left, top, right, _ = win32gui.GetWindowRect(hwnd)

    desktop.click_at((left + right) // 2, top + 20)


def ensure_running(desktop: DesktopBot):
    """Starts Fakturama if it isn't already running, and brings its window to
    the OS foreground - see _focus_window_by_pid()."""
    process = desktop.find_process(name=config.FAKTURAMA_PROCESS_NAME)
    if process is None:
        desktop.execute(config.FAKTURAMA_EXE_PATH)
        for _ in range(30):
            time.sleep(1)
            process = desktop.find_process(name=config.FAKTURAMA_PROCESS_NAME)
            if process:
                break
    if process:
        _focus_window_by_pid(desktop, process.pid)


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
    logger.info(f"Registered contact in Fakturama: {contact['First Name']} {contact['Last Name']}")

    desktop.save_screenshot("./output/fakturama_contact_registered.png")
    logger.info("Saved contact registration evidence screenshot.")


def register_product(desktop: DesktopBot, item: dict):
    """Registers one scraped Sauce Demo product (a row from item_list.csv) as
    a new product in Fakturama."""
    ensure_running(desktop)
    _find_or_raise(desktop, "new_product", waiting_time=15000)
    desktop.click()
    _find_or_raise(desktop, "label_new_product")
    desktop.click()

    desktop.tab(presses=2)
    desktop.kb_type(str(item["Item Number"]))
    desktop.tab(presses=1)
    desktop.kb_type(item["Item Name"])
    desktop.tab(presses=1)
    desktop.kb_type("Shop")
    desktop.tab(presses=3)
    desktop.kb_type(item["Description"])
    desktop.tab(presses=1)
    desktop.kb_type(str(item["Price"]))
    desktop.control_s()
    desktop.control_w()
    logger.info(f"Registered product in Fakturama: {item['Item Name']}")


def capture_products_evidence(desktop: DesktopBot):
    """Opens the Fakturama Products list and screenshots it as evidence that
    every scraped product was registered. Call this once, after every
    register_product() call, while Fakturama is still open."""
    ensure_running(desktop)
    _find_or_raise(desktop, "products_db")
    desktop.click()
    desktop.wait(1000)
    desktop.save_screenshot("./output/fakturama_products_list.png")
    logger.info("Saved Fakturama products list evidence screenshot.")
