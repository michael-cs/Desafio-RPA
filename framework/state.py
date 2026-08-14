from botcity.maestro import BotMaestroSDK, AutomationTaskFinishStatus, AutomationTask
from framework.exceptions import InterruptException
from dataclasses import dataclass, asdict, field
from framework.config import TASK_ID
from botcity.core import DesktopBot
from botcity.web import WebBot
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)

# Loads MAESTRO_URL/MAESTRO_LOGIN/MAESTRO_KEY from a local .env file, if one
# exists. Machine/user-level environment variables (set outside of .env)
# already work without this - load_dotenv() never overrides an existing
# os.environ value, so both setups are safe to use at the same time.
load_dotenv()

'''
state.py
    Implements a state management system that works seamlessly with BotCity Orchestrator features.
'''


@dataclass
class State:
    maestro: BotMaestroSDK = None
    task_id: str = ""
    item: dict = field(default_factory=dict)
    contact: dict = field(default_factory=dict)
    success_count: int = 0
    error_count: int = 0
    has_error: bool = False
    has_success: bool = False
    webbot: WebBot = None
    desktopbot: DesktopBot = None
    datasource = None

    @property
    def total_items(self):
        """Sums success and error items."""
        return self.success_count + self.error_count

    def register_success(self):
        self.has_success = True
        self.success_count += 1

    def register_error(self):
        self.has_error = True
        self.error_count += 1

    def compute_finish_status(self) -> AutomationTaskFinishStatus:
        if self.has_success and self.has_error:
            return AutomationTaskFinishStatus.PARTIALLY_COMPLETED
        elif self.has_error:
            return AutomationTaskFinishStatus.FAILED
        else:
            return AutomationTaskFinishStatus.SUCCESS

    def raise_for_interrupt_requested(self) -> bool:
        task_info = self.maestro.get_task(self.task_id)
        if task_info.is_interrupted():
            raise InterruptException("Interrupt requested via BotCity.")
        return False

    def task_info(self) -> AutomationTask:
        return self.maestro.get_task(self.task_id)

    def as_dict(self):
        return asdict(self)


'''
Initializes the STATE variable based on the execution environment.
Checks if the bot is running in the BotCity Runner environment or locally with/without authentication.
'''

try:
    if BotMaestroSDK.from_sys_args().server != '':
        STATE = State()
        STATE.maestro = BotMaestroSDK.from_sys_args()
        STATE.task_id = STATE.maestro.task_id
        STATE.execution = STATE.maestro.get_execution(STATE.task_id)
        print("\n ######### Bot is running in a BotCity Runner environment. \n")
    elif TASK_ID:
        STATE = State()
        STATE.maestro = BotMaestroSDK.from_sys_args(default_server=os.getenv("MAESTRO_URL"),
                                                    default_login=os.getenv("MAESTRO_LOGIN"),
                                                    default_key=os.getenv('MAESTRO_KEY'), )
        STATE.task_id = TASK_ID
        STATE.execution = STATE.maestro.get_execution(STATE.task_id)
        print("\n ######### Bot is running locally with authentication enabled. \n")
    else:
        raise Exception(
            "No valid environment variables configuration found in the server. Set your credentials in the .env file order to run your bot locally.")
except Exception as e:
    # If any error occurs, we assume the bot is running locally without authentication.
    print(f"Error: {e}")
    STATE = State()
    STATE.maestro = BotMaestroSDK()
    # Disable errors if we are not connected to the Orchestrator
    STATE.maestro.RAISE_NOT_CONNECTED = False
    # Opt-in to receive mock objects when not connected to the Orchestrator
    STATE.maestro.MOCK_OBJECT_WHEN_DISCONNECTED = True
    STATE.execution = STATE.maestro.get_execution(STATE.task_id)
    print("\n ######### Bot is running in test mode (locally without authentication). \n")
