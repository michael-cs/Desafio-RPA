from framework.exceptions import BotException
from fakturama_desktop import desktop as fakturama_desktop
from framework.state import STATE
import logging
import traceback

logger = logging.getLogger(__name__)

'''
process.py
    process_item(item): per-item automation, one call per product scraped
    from the Sauce Demo catalog (assets/item_list.csv) - registers it as a
    new product in Fakturama, replicating the web-scraped master data into
    the desktop system.
'''


def process_item(item):
    """
    Runs the steps of the automation process for each item and checks if the process has received an interruption request from the BotCity Orchestrator.
    """
    STATE.raise_for_interrupt_requested()

    logger.info(f"Item processing has started: {item}.")

    try:
        fakturama_desktop.register_product(STATE.desktopbot, item)
    except BotException as e:
        if e.kwargs:
            logger.info("Exception with kwargs caught. Re-raising with context info...")
            raise type(e)(
                exc_message=f"Error: {str(e.exc_message)}\n{traceback.format_exc()}",
                maestro=STATE.maestro,
                **e.kwargs
            )
        else:
            logger.error("Exception without kwargs caught. Propagating as is.")
            raise type(e)(f"Error: {str(e.exc_message)}\n{traceback.format_exc()}")
    except Exception as e:
        raise e

    return f"{item['Item Name']} registered in Fakturama."


def capture_products_evidence():
    """
    Runs once, after every catalog item has gone through process_item(),
    while Fakturama is still open. Screenshots the full products list as
    evidence that every scraped product was registered.
    """
    logger.info("Capturing Fakturama products list evidence...")
    fakturama_desktop.capture_products_evidence(STATE.desktopbot)
