from botcity.maestro import AlertType
import logging

logger = logging.getLogger(__name__)


def _base_maestro_log(maestro, activity_label: str, supported_keys: set, **kwargs):
    """
    Core function for standardizing BotCity Maestro log entries.
    Filters out unsupported keys and requires at least one valid data point.
    """
    valid_values = {k: v for k, v in kwargs.items() if k in supported_keys}

    invalid_keys = set(kwargs.keys()) - supported_keys
    for key in invalid_keys:
        logger.warning(f"Argument '{key}' is not supported for '{activity_label}' and will be ignored.")

    if not valid_values:
        error_msg = f"No valid arguments provided for '{activity_label}' log."
        logger.error(error_msg)
        raise ValueError(f"{error_msg} At least one of the following keys is required: {supported_keys}")

    maestro.new_log_entry(
        activity_label=activity_label,
        values=valid_values
    )
    logger.info(f"Successfully sent log '{activity_label}' to Maestro with keys: {list(valid_values.keys())}")


def log_warning(maestro, **kwargs):
    """
    Registers a warning log entry in BotCity Maestro for a business/system exception.
    """
    _base_maestro_log(
        maestro=maestro,
        activity_label="Item_Exception",
        supported_keys={"item_number", "item_name", "description", "price"},
        **kwargs
    )


def log_error(maestro, **kwargs):
    """
    Registers a critical error log entry in BotCity Maestro.
    """
    _base_maestro_log(
        maestro=maestro,
        activity_label="Critical_Error",
        supported_keys={"item_number", "item_name", "description", "price", "error_code"},
        **kwargs
    )


def create_alert(maestro, task_id, title, message):
    """
    Creates a WARNING-type alert in the BotCity orchestrator for a specific task.
    """
    maestro.alert(
        task_id=task_id,
        title=title,
        message=message,
        alert_type=AlertType.WARN
    )
