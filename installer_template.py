INSTALLER_TEMPLATE = """
!include "MUI2.nsh"
!include "nsDialogs.nsh"

Name "{APP_FULLNAME}"
OutFile "dist\{finished_app_installer}"
InstallDir "$LOCALAPPDATA\BM\{APP_SHORT_NAME}"
RequestExecutionLevel user  ; 🚫 No admin rights, per-user only

;--------------------------------
; Modern UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "{APP_ICON}"
!define MUI_UNICON "{APP_ICON}"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ".\\imgs\\banner_h.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP ".\\imgs\\banner_v.bmp"
BrandingText "TNR Software"

;--------------------------------
; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!define MUI_FINISHPAGE_SHOW "LaunchPage"
!define MUI_FINISHPAGE_LEAVE "Finish"

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Var LaunchCheckbox

Function LaunchPage
    nsDialogs::Create 1018
    Pop $0
    ${If} $0 == error
        Abort
    ${EndIf}

    ${NSD_CreateCheckBox} 20u 20u 200u 12u "Launch {APP_NAME}"
    Pop $LaunchCheckbox
    ${NSD_SetState} $LaunchCheckbox 1

    nsDialogs::Show
FunctionEnd

Function Finish
    ${NSD_GetState} $LaunchCheckbox $0
    StrCmp $0 1 LaunchApp Done

    LaunchApp:
        Exec "$INSTDIR\{APP_FULLNAME}.exe"

    Done:
        Return
FunctionEnd

;--------------------------------
Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\{APP_FULLNAME}.exe"

    ; Create Start Menu shortcut (user only)
    CreateDirectory "$SMPROGRAMS\{APP_NAME}"
    CreateShortCut "$SMPROGRAMS\{APP_NAME}\{APP_NAME}.lnk" \
        "$INSTDIR\{APP_FULLNAME}.exe" "" "$INSTDIR\{APP_FULLNAME}.exe" 0

    ; Create Desktop shortcut (user only)
    CreateShortCut "$DESKTOP\{APP_NAME}.lnk" \
        "$INSTDIR\{APP_FULLNAME}.exe" "" "$INSTDIR\{APP_FULLNAME}.exe" 0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall_{APP_SHORT_NAME}.exe"

    ; Add to Add/Remove Programs (per-user)
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayName" "{APP_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayVersion" "{APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "UninstallString" "$INSTDIR\Uninstall_{APP_SHORT_NAME}.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "Publisher" "TNR Software"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}" "DisplayIcon" "$INSTDIR\{APP_FULLNAME}.exe"

    ; Set app environment variable (user only)
    WriteRegExpandStr HKCU "Environment" "{APP_SHORT_NAME}" "$INSTDIR"
    System::Call 'user32::SendMessageTimeout(i ${HWND_BROADCAST}, i ${WM_SETTINGCHANGE}, i 0, t "Environment", i 0, i 1000, *i .r0)'
SectionEnd

;--------------------------------
Section "Uninstall"
    ; Delete main app file
    Delete "$INSTDIR\{APP_FULLNAME}.exe"
    
    ; Delete shortcuts
    Delete "$SMPROGRAMS\{APP_NAME}\{APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\{APP_NAME}"
    Delete "$DESKTOP\{APP_NAME}.lnk"

    ; Delete uninstaller
    Delete "$INSTDIR\Uninstall_{APP_SHORT_NAME}.exe"

    ; Remove from Add/Remove Programs
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}"

    ; Remove environment variable
    DeleteRegValue HKCU "Environment" "{APP_SHORT_NAME}"
    System::Call 'user32::SendMessageTimeout(i ${HWND_BROADCAST}, i ${WM_SETTINGCHANGE}, i 0, t "Environment", i 0, i 1000, *i .r0)'

    ; Remove install directory
    RMDir /r "$INSTDIR"
SectionEnd


"""
