import os


__all__ = ["NOTES_DB", "NOTES_FOLDER",
           "RECOVERY_FILE", "pass_file",
             "data_folder", "logs_file"]
data_folder = os.getenv("appdata")
NOTES_FOLDER = os.path.join(data_folder, "Thought Book")  # type: ignore
os.makedirs(NOTES_FOLDER, exist_ok=True)


# Production
NOTES_DB = os.path.join(NOTES_FOLDER, "BMTbnotes.db")



# putting all files here including
# the hashed passwords
RECOVERY_FILE = os.path.join(NOTES_FOLDER, "recovery.key")  # type: ignore
pass_file = os.path.join(NOTES_FOLDER, "pass.pass")  # type: ignore
logs_file = os.path.join(NOTES_FOLDER, "app.log")  # type: ignore