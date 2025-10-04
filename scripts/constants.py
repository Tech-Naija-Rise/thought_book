# constants.py
import os
import json
import uuid
import logging
from pathlib import Path
import sys
import tkinter.messagebox as tkmsg

__all__ = [
    "NOTES_DB", "NOTES_FOLDER",
    "RECOVERY_FILE", "PASS_FILE",
    "DATA_FOLDER", "LOGS_FILE",
    "BMA_DOWNLOAD_LINK", "APP_NAME",
    "APP_VERSION", "APP_ICON", "APP_PHOTO"
]

# --- License Management ---
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnBOjHCBqpuw6de8jvHwv
T9VEdHmVOAxIQMIYjRtJnrhYSwFeN8YpWODDk6mPqOJMsGDApN/oJG4fqNW9NvTr
p3dz0SoU/1tZFMqX7WOqo0EaUiViOzCw3MFe83nnP4OW418+TLcivXlUFvUefxJi
VZ+liHmTPqWIJe1rW596h4yRtzgiTZKFLsvsg1Te6ngSHdwCTSSdcqR6QhQQkYzP
tzsNrK+dDT/IpbPOQ4yniByxqtHFhgXRrvoGZLUyxRetKsTvcfImirYL9rTS8ga3
o2blCB3/0uiqcqq1KaOFwmnEhzh+zGBEecgm23ot3AQlq9VMkSRQBmPLVTjJW3pH
lQIDAQAB
-----END PUBLIC KEY-----

"""

# --- App Info ---
APP_NAME = "Thought Book"
APP_VERSION = "1.0.0"
APP_SHORT_NAME = "BMTB"

# This is the unique id for the app on each individual installation of bmtb
USER_APP_ID = ""  # XXX for freemium purposes.


# --- Helper Functions ---
def resource_path(relative_path: Path) -> Path:
    """Return absolute path to resource (works for dev & PyInstaller)."""
    try:
        # type: ignore # PyInstaller temp folder
        base_path = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


def get_device_id(config_file):
    """Returns a persistent unique ID for this device/app install."""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
                if "device_id" in data:
                    return data["device_id"]
        except Exception:
            pass  # if file corrupted, regenerate

    # Generate new UUID and save it
    device_id = str(uuid.uuid4())
    with open(config_file, "w") as f:
        json.dump({"device_id": device_id}, f)
    return device_id


# --- Main Folders ---
MAIN_FOLDER = Path(__file__).resolve().parent.parent
DEPLOY_INFO_PATH = MAIN_FOLDER / "deploy.info"

# --- Load version if in deploy.info ---
if DEPLOY_INFO_PATH.exists():
    with open(DEPLOY_INFO_PATH, "r", encoding="utf-8") as f:
        deploy_info = json.load(f)
    APP_VERSION = deploy_info.get("app_version", APP_VERSION)

# --- Images & Icons ---
IMGS_FOLDER = MAIN_FOLDER / "imgs"
APP_ICON = resource_path(IMGS_FOLDER / "logo.ico")
APP_PHOTO = IMGS_FOLDER / "logo.png"

# --- Data Storage (always under %APPDATA%/BM) ---
DATA_FOLDER = Path(os.getenv("APPDATA", "")) / "BM"
NOTES_FOLDER = DATA_FOLDER / APP_NAME
NOTES_FOLDER.mkdir(parents=True, exist_ok=True)

HIDDEN_FOLDER = NOTES_FOLDER / f".{APP_SHORT_NAME}"
HIDDEN_FOLDER.mkdir(parents=True, exist_ok=True)


# --- Files ---
# Hidden files
METRICS_FILE = HIDDEN_FOLDER / "metrics.json"  # for freemium model
LICENSE_FILE = HIDDEN_FOLDER / "license.json"
ID_FILE = HIDDEN_FOLDER / "config.json"
EMAIL_ID_FILE = HIDDEN_FOLDER / "email_config.json"


NOTES_DB = NOTES_FOLDER / "BMTbnotes.db"
RECOVERY_FILE = NOTES_FOLDER / "recovery.key"
PASS_FILE = NOTES_FOLDER / "pass.pass"
LOGS_FILE = NOTES_FOLDER / "app.log"
FB_PATH = NOTES_FOLDER / "feedbacks.json"
SETTINGS_FILE = NOTES_FOLDER / "settings.json"


# --- Freemium specification files functionality ---

# config for unique device id
USER_APP_ID = get_device_id(ID_FILE)


# default counts
NOTE_COUNT_LIMIT_FALLBACK = 10
MAX_UPGRADE_REMIND = 1
UPGRADE_REMINDER_COUNT = 0


def hideables(hide=True, file=METRICS_FILE):
    if not hide:
        os.system(f'attrib -H "{HIDDEN_FOLDER}"')  # Hide folder
        os.system(f'attrib -H "{file}"')  # Hide metrics.json
    else:
        os.system(f'attrib +H "{HIDDEN_FOLDER}"')  # Hide folder
        os.system(f'attrib +H "{file}"')  # Hide metrics.json


def write_json_file(file, contents={}):
    """Must be in json"""
    hideables(hide=False)
    with open(file, "w") as w:
        json.dump(contents, w)
    hideables(hide=True)


def read_json_file(file):
    """Must be in json"""
    hideables(hide=False)
    with open(file, "r") as r:
        contents = dict(json.load(r))
    hideables(hide=True)
    return contents


def read_txt_file(file):
    """Must be string"""
    with open(file, "r") as r:
        contents = r.read()
    return contents


def write_txt_file(file, contents=""):
    """Must be string"""
    with open(file, "r") as w:
        w.write(contents)
    return


METRICS_FILE_CONTENT = {
    "note_count_limit": NOTE_COUNT_LIMIT_FALLBACK,
    "max_upgrade_remind": MAX_UPGRADE_REMIND,
    "upgrade_reminder_count": UPGRADE_REMINDER_COUNT}

if not os.path.exists(METRICS_FILE):
    # Put defaults since it is not complete
    write_json_file(METRICS_FILE, METRICS_FILE_CONTENT)
else:
    METRICS_FILE_CONTENT = read_json_file(METRICS_FILE)

# --- Logging ---
logging.basicConfig(
    filename=LOGS_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# --- External Links ---
BMA_DOWNLOAD_LINK = "https://github.com/Mahmudumar/BMA/releases/latest"
BMTB_DOWNLOAD_LINK = "https://github.com/Mahmudumar/thought_book/releases"
BMTB_FEEDBACK_SERVER = "https://feedback-server-tnr.onrender.com/feedback"
TNR_BMTB_SERVER = "https://feedback-server-tnr.onrender.com"


if __name__ == "__main__":
    print(f"Main folder: {MAIN_FOLDER}")
    print(f"Data folder: {DATA_FOLDER}")
    print(f"App version: {APP_VERSION}")
