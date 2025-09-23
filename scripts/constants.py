import os
import logging
import tkinter.messagebox as tkmsg

__all__ = ["NOTES_DB", "NOTES_FOLDER",
           "RECOVERY_FILE", "pass_file",
           "data_folder", "logs_file", "BMA_DOWNLOAD_LINK"]

from pathlib import Path

main_folder = Path(__file__).resolve().parent.parent
app_name = "Thought Book"
app_version = "1.0.0"

imgs_folder = main_folder / "imgs"
app_icon = imgs_folder / "logo.ico"
app_photo = imgs_folder / "logo.png"


data_folder = os.getenv("appdata")

BM_FOLDER = os.path.join(data_folder, "BM") # type: ignore
os.makedirs(BM_FOLDER, exist_ok=True)

NOTES_FOLDER = os.path.join(BM_FOLDER, "Thought Book")  # type: ignore
os.makedirs(NOTES_FOLDER, exist_ok=True)


# Production
NOTES_DB = os.path.join(NOTES_FOLDER, "BMTbnotes.db")


# putting all files here including
# the hashed passwords
RECOVERY_FILE = os.path.join(NOTES_FOLDER, "recovery.key")  # type: ignore
pass_file = os.path.join(NOTES_FOLDER, "pass.pass")  # type: ignore
logs_file = os.path.join(NOTES_FOLDER, "app.log")  # type: ignore
fb_path = os.path.join(NOTES_FOLDER, "feedbacks.json")

logging.basicConfig(
    filename=logs_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info(f"Main folder: {main_folder}")


# They need to see the app too in demo.

# XXX this link will change once i setup the app's git site.
BMA_DOWNLOAD_LINK = "https://github.com/Mahmudumar/BMA/releases/latest"


BMTb_DOWNLOAD_LINK = "https://github.com/Mahmudumar/thought_book/releases"
BMTb_FEEDBACK_SERVER = "https://feedback-server-tnr.onrender.com/feedback"
