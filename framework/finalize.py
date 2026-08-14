from framework.state import STATE
from pathlib import Path
import logging
import glob

logger = logging.getLogger(__name__)

'''
finalize.py
    Gracefully ends the automation process using Cleanup and Finalize steps.
'''


def cleanup():
    """
    Closes the browser. Called both on SystemException restarts and at the
    very end of the run, so it must stay safe to call more than once.
    """
    try:
        logger.info("Cleaning up...")
        if STATE.webbot:
            STATE.webbot.stop_browser()
            logger.info("Browser closed.")
    except Exception as ex:
        logger.error(f"Error during cleanup: {ex}")
        raise ex


def finalize():
    """
    Performs steps to finalize the automation process gracefully in the BotCity Orchestrator.
    """
    try:
        logger.info(
            f"The automation process has finished. Task ID: {STATE.task_id}. {finish_status_message()}")

        try:
            STATE.maestro.new_log_entry(
                STATE.task_info().activity_name, {
                    "message": finish_status_message()})
        except Exception as ex:
            logger.error(
                f"Error while trying to create a new log entry in the BotCity Orchestrator: {ex}")

        upload_output_orchestrator()

    except Exception as ex:
        logger.error(f"Error during finalize: {ex}")
        raise ex
    finally:
        finish_task_orchestrator()
        print(finish_status_message())


def upload_output_orchestrator():
    """Uploads the whole output folder (logs, result CSV, audit screenshots) to BotCity Orchestrator."""
    try:
        logger.info("Uploading output to BotCity Orchestrator as Result Files...")
        for f in glob.iglob("./output/*"):
            fp = Path(f)
            STATE.maestro.post_artifact(
                task_id=STATE.task_id,
                artifact_name=fp.name,
                filepath=fp
            )
    except Exception as ex:
        print(f"Error uploading output to BotCity Orchestrator: {ex}")
        raise ex


def finish_task_orchestrator():
    try:
        STATE.maestro.finish_task(
            task_id=STATE.task_id,
            status=STATE.compute_finish_status(),
            message=finish_status_message(),
            total_items=STATE.total_items,
            processed_items=STATE.success_count,
            failed_items=STATE.error_count
        )
    except Exception as ex:
        print(f"Error finishing task in the BotCity Orchestrator: {ex}")
        raise ex


def finish_status_message() -> str:
    try:
        msg = f''' Task Completed - Process: {STATE.task_info().activity_name}.
        In our run for task {STATE.task_id} we processed {STATE.total_items} items, from which {STATE.success_count} were with success.
        Check the Result Files for more details.
        '''
        return msg
    except Exception as ex:
        logger.error(f"Error generating finish status message: {ex}")
        return "Task completed. Check the Result Files for more details."
