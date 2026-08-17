from fakturama_desktop import desktop as fakturama_desktop
from framework.state import STATE
from framework import config
from pathlib import Path
import logging
import shutil
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


def close_fakturama():
    """
    Closes Fakturama at the very end of a successful run. Every contact/product
    registration already saves itself individually (ctrl+s), so there's no
    final "save all" step needed here - just closing the app.
    """
    try:
        if STATE.desktopbot:
            process = STATE.desktopbot.find_process(name=config.FAKTURAMA_PROCESS_NAME)
            if process:
                STATE.desktopbot.terminate_process(process)
                logger.info("Fakturama closed.")
    except Exception as ex:
        logger.error(f"Error closing Fakturama: {ex}")


def copy_generated_csvs_to_output():
    """
    Copies the scraped buyer/catalog CSVs into ./output/ so they're uploaded
    to BotCity Orchestrator as task evidence, alongside the log/result CSV
    and the Fakturama screenshots.
    """
    for src in (config.CSV_CONTACT, config.CSV_ITEMS):
        try:
            if Path(src).exists():
                shutil.copy(src, "./output/" + Path(src).name)
                logger.info(f"Copied {src} to output/ as evidence.")
        except Exception as ex:
            logger.error(f"Error copying {src} to output/: {ex}")


def finalize():
    """
    Performs steps to finalize the automation process gracefully in the BotCity Orchestrator.
    """
    try:
        logger.info(
            f"The automation process has finished. Task ID: {STATE.task_id}. {finish_status_message()}")

        close_fakturama()
        copy_generated_csvs_to_output()

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
        # Best-effort reporting step, called from finalize()'s own `finally`
        # clause - a transient network/Orchestrator failure here must not
        # crash the process and hide whether the actual automation succeeded.
        print(f"Error uploading output to BotCity Orchestrator: {ex}")


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
        # Same reasoning as upload_output_orchestrator() above.
        print(f"Error finishing task in the BotCity Orchestrator: {ex}")


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
