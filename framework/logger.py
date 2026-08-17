from botcity.maestro import Column
from framework.state import STATE
import datetime
import logging

logger = logging.getLogger(__name__)

'''
Logger
    Configure logging for the automation process: file-based logs in output/ and
    BotCity's built-in Execution Log.
'''


def log_result_file() -> str:
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    task_id = STATE.task_id
    return f".\\output\\Log_BotCity_task-{task_id}_date-{date}.log"


def setup_logger():
    log_file = log_result_file()
    logging.basicConfig(filename=log_file,
                        level=logging.INFO,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        encoding='utf-8'
                        )
    logger.info(f"Log created at {log_file}.")


def setup_botcity_log():
    try:
        STATE.maestro.new_log(STATE.task_info().activity_name, [
            Column("Message", "message", 100)])
        logger.info(f"BotCity log created \"{STATE.task_info().activity_name}\"")
    except Exception as ex:
        logger.error(f"{ex} (The log \"{STATE.task_info().activity_name}\" probably already exists.)")
        pass
