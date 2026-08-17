from pathlib import Path

# Process settings
# BotCity Maestro test task on the personal tenant (MAESTRO_URL/LOGIN/KEY come
# from the machine's environment variables - see framework/state.py).
TASK_ID = "25059164"
ACTIVITY_NAME = "Desafio RPA - Sauce Demo to Fakturama"

# Sauce Demo (e-commerce under test)
# NOTE: the old /v1/ path now just redirects to the root - pointing at the
# canonical URL directly avoids an extra redirect hop during automation.
SAUCE_DEMO_URL = "https://www.saucedemo.com/"
SAUCE_DEMO_USER = "standard_user"
SAUCE_DEMO_PASSWORD = "secret_sauce"

# Fake buyer generator
FAKE_NAME_GENERATOR_URL = "https://www.fakenamegenerator.com/gen-random-br-br.php"

# Fakturama desktop app
FAKTURAMA_EXE_PATH = r"C:\Program Files\Fakturama2\Fakturama.exe"
FAKTURAMA_PROCESS_NAME = "Fakturama.exe"

# File Settings
ASSETS_FOLDER = str(Path(__file__).parent.parent) + "\\assets\\"
IMAGES_FOLDER = ASSETS_FOLDER + "images\\"
CSV_CONTACT = ASSETS_FOLDER + "contact_list.csv"
CSV_ITEMS = ASSETS_FOLDER + "item_list.csv"
OUTPUT_FOLDER = str(Path(__file__).parent.parent) + "\\output\\"
