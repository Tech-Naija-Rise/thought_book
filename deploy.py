# deploy.py
import os
import shutil
from pathlib import Path
from scripts.constants import app_name

NSIS_TEMPLATE = r"""
!include "MUI2.nsh"

Name "{app_name}"
OutFile "dist\{app_name}_Installer.exe"
InstallDir "$PROGRAMFILES\{app_name}"
RequestExecutionLevel user

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\{app_name}.exe"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\{app_name}"
    CreateShortCut "$SMPROGRAMS\{app_name}\{app_name}.lnk" "$INSTDIR\{app_name}.exe" "" "$INSTDIR\{app_name}.exe" 0 SW_SHOWNORMAL "" "CTRL+ALT+T"

    ; Desktop shortcut with hotkey
    CreateShortCut "$DESKTOP\{app_name}.lnk" "$INSTDIR\{app_name}.exe" "" "$INSTDIR\{app_name}.exe" 0 SW_SHOWNORMAL "" "CTRL+ALT+T"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\{app_name}.exe"
    Delete "$SMPROGRAMS\{app_name}\{app_name}.lnk"
    RMDir "$SMPROGRAMS\{app_name}"
    Delete "$DESKTOP\{app_name}.lnk"
    RMDir "$INSTDIR"
SectionEnd
"""

def build_exe(script_path="notes_app.py"):
    exe_dir = Path("dist")
    exe_dir.mkdir(exist_ok=True)

    cmd = f'pyinstaller --noconfirm -n "{app_name}" --noconsole --onefile "{script_path}"'
    print(cmd)
    os.system(cmd)

    # cleanup
    for item in ["build", "__pycache__", f"{app_name}.spec"]:
        p = Path(item)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)

    return exe_dir / f"{app_name}.exe"

def write_nsi():
    nsi_path = Path("dist") / f"{app_name}.nsi"
    with open(nsi_path, "w", encoding="utf-8") as f:
        f.write(NSIS_TEMPLATE.format(app_name=app_name))
    print(f"NSIS script written: {nsi_path}")
    return nsi_path

def compile_installer(nsi_path):
    os.system(f'makensis "{nsi_path}"')

def main():
    exe_path = build_exe()
    print(f"Built exe: {exe_path}")
    nsi_path = write_nsi()
    compile_installer(nsi_path)
    print("Installer built successfully.")

if __name__ == "__main__":
    main()
