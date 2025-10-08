# dialogs_manager.py
"""The place where all BMTB dialogs are managed from."""

import customtkinter as ctk
import tkinter.messagebox as tkmsg
import tkinter.commondialog as tkcd
from scripts.constants import APP_ICON, APP_NAME, APP_SHORT_NAME, APP_VERSION


# We just want control over the buttons of the dialog for
# now that's all. so we will display it as is but with custom 
# buttons that i can manually assign commands to.
