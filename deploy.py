# deploy.py
import os
import shutil
from pathlib import Path
import sys
from scripts.constants import app_name, app_icon, app_version, app_icon_production

# The installer must have the following:
# 1. assign a shortcut in desktop with a hotkey of ctrl+alt+t
# 2. assign a shortcut in start menu with a hotkey of ctrl+alt+t

# 3. make the abbreviation BMTB to be in Path environment variable
# 4. add windows registry for windows to recognize and accordingly
# remove the app from windows settings

finished_app_installer = "BMTB_Installer_" + app_version + ".exe"

NSIS_INSTALLER_TEMPLATE = r"""
!include "MUI2.nsh"
!include nsDialogs.nsh

Name "{app_name}"
OutFile "dist\{finished_app_installer}"
InstallDir "$PROGRAMFILES\BM\BMTB"
RequestExecutionLevel admin

;--------------------------------
; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON {app_icon}
!define MUI_UNICON {app_icon}
!define MUI_HEADERIMAGE

;--------------------------------
; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES


!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"



Var LaunchCheckbox

Page custom LaunchPage Finish

Function LaunchPage
    nsDialogs::Create 1018
    Pop $0
    ${{If}} $0 == error
        Abort
    ${{EndIf}}

    ; Create the checkbox
    ${{NSD_CreateCheckBox}} 20u 20u 200u 12u "Launch {app_name}"
    Pop $LaunchCheckbox
    ${{NSD_SetState}} $LaunchCheckbox 1 ; checked by default

    nsDialogs::Show
FunctionEnd

Function Finish
    ; Check if checkbox is checked and launch app
    ${{NSD_GetState}} $LaunchCheckbox $0
    StrCmp $0 1 LaunchApp Done
    Done:
    Return

    LaunchApp:
    Exec "$INSTDIR\{app_name}.exe"
FunctionEnd





;--------------------------------
Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\{app_name}.exe"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\{app_name}"
    CreateShortCut "$SMPROGRAMS\{app_name}\{app_name}.lnk"\
    "$INSTDIR\{app_name}.exe" "" "$INSTDIR\{app_name}.exe" 0 SW_SHOWNORMAL "" "3+T"

    ; Desktop shortcut
    CreateShortCut "$DESKTOP\{app_name}.lnk"\
    "$INSTDIR\{app_name}.exe" "" "$INSTDIR\{app_name}.exe" 0 SW_SHOWNORMAL "" "3+T"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_BMTB.exe"

    ; ----------------------------
    
    
    ; Add registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "DisplayName" "{app_name}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "UninstallString" "$INSTDIR\Uninstall_BMTB.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}" "Publisher" "TNR Software"

    ; make a "Launch {app_name}" checkbutton in the final installer page


SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\{app_name}.exe"
    Delete "$SMPROGRAMS\{app_name}\{app_name}.lnk"
    RMDir "$SMPROGRAMS\{app_name}"
    Delete "$DESKTOP\{app_name}.lnk"

    ; ----------------------------
    
    ; Remove registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{app_name}"

    Delete "$INSTDIR\*.*"  ; delete all files
    RMDir "$INSTDIR"       ; remove directory
SectionEnd

"""


def build_exe(script_path="notes_app.py"):
    exe_dir = Path("dist")
    exe_dir.mkdir(exist_ok=True)
    # when building, make sure that we have the extra data which is the icon
    # and any other files that the app might need

    cmd = f'pyinstaller --noconfirm -i "{app_icon}"'
    cmd += f' --add-data "{app_icon};imgs" -n "{app_name}"'
    cmd += f' --noconsole --onefile "{script_path}"'
    print(cmd)
    os.system(cmd)

    # cleanup
    for item in ["build", "__pycache__"]:
        p = Path(item)
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.is_file():
            p.unlink(missing_ok=True)

    return exe_dir / f"{app_name}.exe"


def write_nsi():
    nsi_path = Path(".") / f"{app_name}.nsi"
    with open(nsi_path, "w", encoding="utf-8") as f:
        f.write(NSIS_INSTALLER_TEMPLATE.format(
            app_name=app_name,
            app_icon=app_icon,
            finished_app_installer=finished_app_installer,
        ))
    print(f"NSIS script written: {nsi_path}")
    return nsi_path


def compile_installer(nsi_path):
    os.system(f'makensis "{nsi_path}"')


def main():
    # exe_path = build_exe()
    # print(f"Built exe: {exe_path}")
    nsi_path = write_nsi()
    compile_installer(nsi_path)
    print("Installer built successfully.")

    # Move the made installer to a special folder where all finished
    # apps are stored
    output_dir = Path("C:\\Users\\USER\\Documents\\PROGRAMMING\\FINISHED APPS")
    output_dir.mkdir(exist_ok=True)
    installer_path = Path("dist") / finished_app_installer
    if installer_path.exists():
        shutil.move(str(installer_path), str(
            output_dir / finished_app_installer))
        print(f"Installer moved to: {output_dir / finished_app_installer}")
    else:
        print("Installer not found! Probably already moved or build failed.")


if __name__ == "__main__":
    main()
