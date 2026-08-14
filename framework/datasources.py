from botcity.plugins.csv import BotCSVPlugin
from botcity.maestro import ErrorType
from framework.state import STATE
import datetime
import logging

logger = logging.getLogger(__name__)

'''
datasources.py
    Provides the CSVSource used to iterate the order items.

    NOTE: unlike the plain BeaPro template, `data_source` is NOT built at import
    time here. Our input file (assets/order_list.csv) only exists after
    framework.initialize() has generated the fake buyer, scraped the Sauce Demo
    catalog and randomly picked the products to purchase - all of which need the
    WebBot already running. So `data_source` starts as None and is assigned by
    framework.initialize() once assets/order_list.csv has been written.
    Consumers must reference `datasources.data_source` (the module), not import
    the name directly, otherwise they would keep a stale `None` reference.
'''


class BaseSource():
    """Base source for batch processing of items."""

    def report_success(self, status_message):
        raise NotImplementedError

    def report_error(self, error_type, status_message):
        raise NotImplementedError


class CSVSource(BaseSource):
    def __init__(self, file: str):
        self._file = file
        self.csv = BotCSVPlugin()
        self.csv_out = BotCSVPlugin()
        self.csv.read(file)
        self.csv_out_file = self.csv_result_file()
        self.csv_out.set_header(
            self.csv.header + ["TIMESTAMP", "STATUS", "MESSAGE"])
        self.index = 0
        self.count = len(self.csv.as_dataframe().index)
        self.current_item = None

    def __str__(self):
        return f"CSV {self._file}"

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= self.count:
            logger.info(f"CSV {self._file} has no more items.")
            raise StopIteration
        item = self.csv.as_dataframe().loc[self.index].to_dict()
        self.index += 1
        STATE.item = item
        self.current_item = item
        return item

    def _report(self, status, status_message):
        if not self.current_item:
            return

        self.current_item.update({
            "TIMESTAMP": datetime.datetime.now().isoformat(),
            "STATUS": status,
            "MESSAGE": status_message
        })
        self.csv_out.add_row(self.current_item)
        self.csv_out.write(self.csv_out_file)

    def report_success(self, status_message):
        return self._report("SUCCESS", status_message)

    def report_error(self, error_type, status_message):
        return self._report(error_type, status_message)

    def csv_result_file(self):
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        task_id = STATE.task_id
        return f"./output/CSV_BotCity_task-{task_id}_date-{date}.csv"


# Assigned by framework.initialize() once assets/order_list.csv has been generated.
data_source = None
