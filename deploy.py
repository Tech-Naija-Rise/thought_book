
import os
import shutil

from pathlib import Path
import win32com.client


app_name = "Thought Book"


def build_exe(script_path):
    script_path = Path(script_path).resolve()
    hidden_imports = ["autoai"]

    hidden_flags = " ".join(
        [f"--hidden-import {mod}" for mod in hidden_imports])


    cmd = f'pyinstaller --noconfirm -n "{app_name}" --onefile --hide-console hide-early "{script_path}"'
    print(cmd)
    os.system(cmd)

    # cleanup unwanted artifacts
    for item in ["build", "__pycache__", f"{app_name}.spec"]:
        p = Path(item)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)

    return script_path.parent / "dist" / (app_name + ".exe")


def create_shortcut(target, shortcut_path, hotkey=None, workdir=None, description="", icon=None):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(str(shortcut_path))
    shortcut.TargetPath = str(target)
    shortcut.WorkingDirectory = str(workdir or Path(target).parent)
    shortcut.Description = description
    if hotkey:
        shortcut.Hotkey = hotkey  # format "CTRL+ALT+N"

    if icon:
        # icon can be "C:\\Windows\\System32\\shell32.dll,XX"
        shortcut.IconLocation = icon

    shortcut.save()
    return shortcut_path


def main():
    # 1. Build exe
    exe_path = build_exe("notes_app.py")
    print(f"Built exe at: {exe_path}")

    # 2. Create shortcut on Desktop
    desktop = Path.home() / "Desktop"
    shortcut_path = desktop / f"{app_name}.lnk"
    create_shortcut(
        target=exe_path,
        shortcut_path=shortcut_path,
        hotkey="CTRL+ALT+T",  # Control + Alt + T (think)
        description="Launch Thought Book: A place to think in peace",
        # 172 = “computer with speech bubble” on most systems
        icon=r"C:\Windows\System32\shell32.dll,172"
    )
    print(f"Shortcut created: {shortcut_path}")


if __name__ == "__main__":
    main()
