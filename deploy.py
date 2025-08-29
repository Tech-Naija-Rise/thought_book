
import os
import sys
from pathlib import Path
import win32com.client


def build_exe(script_path):
    script_path = Path(script_path).resolve()
    cmd = f'pyinstaller -n "Thought Book" --onefile --noconsole "{script_path}"'
    os.system(cmd)
    return script_path.parent / "dist" / (script_path.stem + ".exe")


def create_shortcut(target, shortcut_path, hotkey=None, workdir=None, description=""):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str(target)
    shortcut.WorkingDirectory = str(workdir or Path(target).parent)
    shortcut.Description = description
    if hotkey:
        shortcut.Hotkey = hotkey  # format "CTRL+ALT+N"
    shortcut.save()
    return shortcut_path


def main():
    # 1. Build exe
    exe_path = build_exe("notes_app.py")
    print(f"Built exe at: {exe_path}")

    # 2. Create shortcut on Desktop
    desktop = Path.home() / "Desktop"
    shortcut_path = desktop / "NotesApp.lnk"
    create_shortcut(
        target=exe_path,
        shortcut_path=shortcut_path,
        hotkey="CTRL+ALT+T", # Control + Alt + T (think)
        description="Launch Thought Book: A place to think in peace"
    )
    print(f"Shortcut created: {shortcut_path}")


if __name__ == "__main__":
    main()
