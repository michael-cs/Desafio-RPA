from framework.status_handling import handle_interrupt_requested, handle_business_exception, handle_system_exception, register_success
from framework.exceptions import BusinessException, SystemException, InterruptException
from framework.process import process_item, finish_transaction
from framework.finalize import cleanup, finalize
from framework.initialize import initialize
from framework import datasources
import logging

logger = logging.getLogger(__name__)

"""Desafio RPA - Sauce Demo to Fakturama

Collects the Sauce Demo product catalog, generates a fake Brazilian buyer,
purchases 3 randomly picked products on the site and replicates the exact
same order in Fakturama, producing audit evidence (screenshots + PDF) that
both purchases match.

Built on top of the BeaPro (BotCity Enterprise Automation) framework - see
framework/ for state management, exception handling, logging and reporting.
To customize this automation:
- Web/desktop business logic lives in ecommerce/ and fakturama_desktop/
- The one-time setup (fake buyer, catalog scraping, order pick, Fakturama
  contact/catalog/order registration) lives in framework/initialize.py::bootstrap()
- The per-item logic lives in framework/process.py::process_item()
"""


def action():
    try:
        initialize()

        # framework.datasources.data_source is only assigned inside initialize(),
        # once assets/order_list.csv exists - see framework/datasources.py.
        for item in datasources.data_source:

            try:
                result_message = process_item(item)
            except InterruptException as ex:
                handle_interrupt_requested(ex)
            except BusinessException as ex:
                handle_business_exception(ex)
            except (SystemException, Exception) as ex:
                handle_system_exception(ex)
                initialize(restart=True)
            else:
                register_success(f"Item processed successfuly: {result_message}")

        finish_transaction()

    except Exception as ex:
        logger.error(f"Error: {ex}")

    finally:
        cleanup()
        finalize()


if __name__ == "__main__":
    action()
