# constants.py
import os
import json
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

# --- App Info ---
APP_NAME = "Thought Book"
APP_VERSION = "1.0.0"
APP_SHORT_NAME = "BMTB"

# --- Resource Path Helper ---


def resource_path(relative_path: Path) -> Path:
    """Return absolute path to resource (works for dev & PyInstaller)."""
    try:
        # type: ignore # PyInstaller temp folder
        base_path = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        base_path = Path(__file__).resolve().parent.parent
    return base_path / relative_path


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

# --- Files ---
NOTES_DB = NOTES_FOLDER / "BMTbnotes.db"
RECOVERY_FILE = NOTES_FOLDER / "recovery.key"
PASS_FILE = NOTES_FOLDER / "pass.pass"
LOGS_FILE = NOTES_FOLDER / "app.log"
FB_PATH = NOTES_FOLDER / "feedbacks.json"
SETTINGS_FILE = NOTES_FOLDER / "settings.json"

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

if __name__ == "__main__":
    print(f"Main folder: {MAIN_FOLDER}")
    print(f"Data folder: {DATA_FOLDER}")
    print(f"App version: {APP_VERSION}")
