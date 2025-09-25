# deploy.py
import json
import os
import re
import shutil
from pathlib import Path
import sys
from scripts.constants import APP_NAME, APP_ICON, APP_VERSION

# -----------------------------------------
# This is info to save whenever i deploy so that the version number increases
# dynamically deploy by deploy. The change_made is one of major
# minor or patch 1.0.0

# First we ask if the changes made were patches or minor or major
deploy_info = {
    "APP_NAME": APP_NAME,
    "APP_VERSION": APP_VERSION,
    "change_made": "patch"
}

if os.path.exists("deploy.info"):
    with open("deploy.info", "r") as rr:
        deploy_info = json.load(rr)

print(deploy_info)
# -----------------------------------------


NSIS_INSTALLER_TEMPLATE = r"""
!include "MUI2.nsh"
!include nsDialogs.nsh


Name "{APP_NAME}"
OutFile "dist\{finished_app_installer}"
InstallDir "$PROGRAMFILES\BM\BMTB"
RequestExecutionLevel admin

;--------------------------------
; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON {APP_ICON}
!define MUI_UNICON {APP_ICON}
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
    ${{NSD_CreateCheckBox}} 20u 20u 200u 12u "Launch {APP_NAME}"
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
    Exec "$INSTDIR\{APP_NAME}.exe"
FunctionEnd





;--------------------------------
Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\{APP_NAME}.exe"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\{APP_NAME}"
    
    CreateShortCut "$SMPROGRAMS\{APP_NAME}\{APP_NAME}.lnk"\
    "$INSTDIR\{APP_NAME}.exe" "" "$INSTDIR\{APP_NAME}.exe" 0 SW_SHOWNORMAL "CTRL|ALT|T" "A place to store your thoughts"

    ; Desktop shortcut
    CreateShortCut "$DESKTOP\{APP_NAME}.lnk"\
    "$INSTDIR\{APP_NAME}.exe" "" "$INSTDIR\{APP_NAME}.exe" 0 SW_SHOWNORMAL "CTRL|ALT|T" "A place to store your thoughts"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_BMTB.exe"

    ; ----------------------------

    ; Set a unique variable for your app's install path
    WriteRegExpandStr HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "BMTB" "$INSTDIR"

    ; Notify system about env change
    SendMessage ${{HWND_BROADCAST}} ${{WM_SETTINGCHANGE}} 0 "STR:Environment"

        

    ; Add registry for Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayName" "{APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayVersion" "{APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "UninstallString" "$INSTDIR\Uninstall_BMTB.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "Publisher" "TNR Software"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayIcon" "$INSTDIR\{APP_NAME}.exe"

SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\{APP_NAME}.exe"
    Delete "$SMPROGRAMS\{APP_NAME}\{APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\{APP_NAME}"
    Delete "$DESKTOP\{APP_NAME}.lnk"

    ; ----------------------------
    ; Remove the unique variable
    DeleteRegValue HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment" "BMTB"

    
    SendMessage ${{HWND_BROADCAST}} ${{WM_SETTINGCHANGE}} 0 "STR:Environment"



    ; Remove registry entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"

    RMDir /r "$INSTDIR"
SectionEnd

"""

# CreateShortCut "$DESKTOP\{APP_NAME}.lnk"\
# "$INSTDIR\{APP_NAME}.exe" "" ["$INSTDIR\{APP_NAME}.exe" 0 SW_SHOWNORMAL "" "3+T"]
# CreateShortCut "link.lnk" "target.exe" [parameters] [icon_file [icon_index [start_options [keyboard_shortcut [description]]]]]


def build_exe(script_path="notes_app.py", d_i=deploy_info):
    exe_dir = Path("dist")
    exe_dir.mkdir(exist_ok=True)
    # when building, make sure that we have the extra data which is the icon
    # and any other files that the app might need

    cmd = f'pyinstaller --noconfirm -i "{APP_ICON}"'
    cmd += f' --add-data "{APP_ICON};imgs" -n "{APP_NAME}"'
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

    return exe_dir / f"{APP_NAME}.exe"


def write_nsi(d_i=deploy_info):
    APP_NAME = d_i['APP_NAME']
    APP_VERSION = d_i['APP_VERSION']

    finished_app_installer = "BMTB_Installer_" + APP_VERSION + ".exe"
    nsi_path = Path(".") / f"{APP_NAME}.nsi"

    with open(nsi_path, "w", encoding="utf-8") as f:
        f.write(NSIS_INSTALLER_TEMPLATE.format(
            APP_NAME=APP_NAME,
            APP_VERSION=APP_VERSION,
            APP_ICON=APP_ICON,
            finished_app_installer=finished_app_installer,
        ))

    print(f"NSIS script written: {nsi_path}")
    return nsi_path, APP_NAME, APP_VERSION, finished_app_installer


# Your demo is not to show off your product,
# it is to convince your audience that you can help
# them solve their problems.

def compile_installer(nsi_path):
    os.system(f'makensis "{nsi_path}"')


def confirm_version():
    start = input(
        "What kind of changes have you made? "
        "(0: no changes, 1: major, 2: minor, 3: patch) > ")

    if start == "1":
        start = "major"
        deploy_info['APP_VERSION'] = deploy_info['APP_VERSION'].split(  # type: ignore
            '.')
        deploy_info['APP_VERSION'][0] = str(  # type: ignore
            int(deploy_info['APP_VERSION'][0]) + 1)
        deploy_info['APP_VERSION'] = '.'.join(deploy_info['APP_VERSION'])

    elif start == "2":
        start = "minor"
        deploy_info['APP_VERSION'] = deploy_info['APP_VERSION'].split(  # type: ignore
            '.')
        deploy_info['APP_VERSION'][1] = str(  # type: ignore
            int(deploy_info['APP_VERSION'][1]) + 1)
        deploy_info['APP_VERSION'] = '.'.join(deploy_info['APP_VERSION'])

    elif start == "3":
        start = "patch"
        deploy_info['APP_VERSION'] = deploy_info['APP_VERSION'].split(  # type: ignore
            '.')
        deploy_info['APP_VERSION'][2] = str(  # type: ignore
            int(deploy_info['APP_VERSION'][2]) + 1)
        deploy_info['APP_VERSION'] = '.'.join(deploy_info['APP_VERSION'])

    elif start == "0":
        print("No changes made, exiting.")
        sys.exit()

    elif re.match(r"[0-9].[0-9].[0-9]", start) is not None:
        print("Making program as is with "
              f"the explicit version number {start}")
        deploy_info['APP_VERSION'] = start.strip()
    
    
    deploy_info['change_made'] = start
    return start


def main():

    start = confirm_version()

    # print("\n", "---"*20)
    # print(f"Making {start} changes to the app...")
    # print(f"Version: {deploy_info['APP_VERSION']}")
    # print("---"*20, "\n")

    # print("---"*20)
    # # Build the executable
    # print("Building the executable...")
    # exe_path = build_exe(d_i=deploy_info)
    # print(f"Built exe: {exe_path}")
    # print("---"*20)

    # Make the nsis and compile it
    print("Writing NSIS script...")
    nsi_path, APP_NAME, APP_VERSION, finished_app_installer = write_nsi(
        d_i=deploy_info)
    compile_installer(nsi_path)
    print(f"Installer built successfully. {finished_app_installer} is ready!")

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

    # The last deploy info saved so it can be
    # started from here or optionally, setting a custom
    # version
    with open("deploy.info", "w") as ww:
        json.dump(deploy_info, ww)
