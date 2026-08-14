from botcity.maestro import AlertType
from framework.state import STATE
from framework import datasources
import datetime
import logging

logger = logging.getLogger(__name__)
maestro = STATE.maestro

'''
status_handling.py
    Provides exception handling, error reporting, and success registration.

    NOTE: imports the `datasources` module (not `data_source` directly), since
    framework.datasources.data_source is only assigned once framework.initialize()
    has generated assets/order_list.csv - see framework/datasources.py.
'''


def handle_business_exception(exception: Exception):
    STATE.register_error()
    datasources.data_source.report_error("BUSINESS EXCEPTION", exception)
    logger.error(f"Business Exception {exception} occurred for item {STATE.item}.")
    maestro.alert(
        task_id=STATE.task_id,
        title="Business Exception ocurred.",
        message=f"Exception: {exception}, Item: {STATE.item}.",
        alert_type=AlertType.ERROR)
    screenshot_error_report(exception)


def handle_system_exception(exception: Exception):
    STATE.register_error()
    datasources.data_source.report_error("SYSTEM EXCEPTION", exception)
    logger.error(f"System Exception {exception} occurred for item {STATE.item}.")
    maestro.alert(
        task_id=STATE.task_id,
        title="System Exception ocurred.",
        message=f"Check the logs for more information. Item: {STATE.item}.",
        alert_type=AlertType.ERROR)
    screenshot_error_report(exception)


def handle_interrupt_requested(exception: Exception):
    STATE.register_error()
    datasources.data_source.report_error("INTERRUPTION REQUESTED", exception)
    logger.warning("Interruption requested via the BotCity Orchestrator.")
    maestro.alert(
        task_id=STATE.task_id,
        title="Interruption requested.",
        message="Interruption requested via the BotCity Orchestrator. Check the logs for more information.",
        alert_type=AlertType.WARN)
    raise exception


def screenshot_error_report(exception):
    """Tries to save a screenshot and registers the error in the BotCity Orchestrator."""
    try:
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_filepath = f".\\temp\\error-{date}.png"
        STATE.desktopbot.save_screenshot(screenshot_filepath)
        maestro.error(task_id=STATE.task_id, exception=exception, screenshot=screenshot_filepath)
    except Exception as ex:
        logger.error(f"Error: {ex}. Uploading error without a screenshot.")
        maestro.error(task_id=STATE.task_id, exception=exception)


def register_success(message):
    """Logs a successful item processing and records it in State and Datasource."""
    logger.info(f"Item processing successfull: item: {STATE.item}, {message}")
    STATE.register_success()
    datasources.data_source.report_success(message)
