from framework import execution_logs
import logging

logger = logging.getLogger(__name__)

'''
Exceptions
    Custom exception hierarchy for categorizing bot errors:
    - BotException: For exceptions that have to be logged in a custom way in the orch
    - BusinessException: For business logic and validation errors
    - SystemException: For technical/infrastructure failures
    - InterruptException: For process interruptions and cancellations
'''


class BotException(RuntimeError):
    """
    Base custom exception for the automation bot.

    This class extends RuntimeError to provide integrated logging capabilities.
    It accepts arbitrary process-specific data via **kwargs (e.g., item_number,
    item_name) and automatically passes it to a class-level logging callback
    if both the callback and a Maestro instance are provided.

    Subclasses should override the `log_callback` attribute with a specific
    logging function (e.g., Maestro's new_log_entry).
    """
    # Define a default callback at the class level (None for the base class)
    log_callback = None

    def __init__(self, exc_message: str, maestro=None, **kwargs):
        self.exc_message = exc_message
        self.maestro = maestro
        self.kwargs = kwargs

        # Trigger the callback if maestro, the callback itself, and kwargs are present
        if maestro and self.log_callback and kwargs:
            self.log_callback(maestro=maestro, **kwargs)

        super().__init__(exc_message)


class BusinessException(BotException):
    """Business rule violations (e.g. product not found on the catalog)."""
    log_callback = staticmethod(execution_logs.log_warning)


class SystemException(BotException):
    """System crashes or Selector/image-matching errors."""
    log_callback = staticmethod(execution_logs.log_warning)


class InterruptException(RuntimeError):
    ...
