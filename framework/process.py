from framework.exceptions import SystemException, BusinessException, BotException
from fakturama_desktop import desktop as fakturama_desktop
from framework.state import STATE
from ecommerce import sauce_demo
import logging
import traceback

logger = logging.getLogger(__name__)

'''
process.py
    process_item(item): per-item automation, one call per product randomly
    picked for the order (assets/order_list.csv) - adds it to the Sauce Demo
    cart and types it into the already-open Fakturama order.

    finish_transaction(): runs once, after every item has gone through
    process_item(), while the browser/Fakturama are still open. It completes
    the Sauce Demo checkout and saves/exports the Fakturama order, producing
    the audit evidence that both purchases match. It intentionally lives
    outside of framework/finalize.py's cleanup(), since cleanup() also runs on
    SystemException restarts (mid-run) and must not trigger the checkout early.
'''


def process_item(item):
    """
    Runs the steps of the automation process for each item and checks if the process has received an interruption request from the BotCity Orchestrator.
    """
    STATE.raise_for_interrupt_requested()

    logger.info(f"Item processing has started: {item}.")

    try:
        sauce_demo.add_to_cart(STATE.webbot, item)
        fakturama_desktop.add_order_line(STATE.desktopbot, item)
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

    result_message = f"{item['Item Name']} added to cart (Sauce Demo) and to the order (Fakturama)."
    return result_message


def finish_transaction():
    logger.info("Finishing the Sauce Demo checkout and the Fakturama order...")
    sauce_demo.checkout(STATE.webbot, STATE.contact)
    fakturama_desktop.finish_order(STATE.desktopbot)
