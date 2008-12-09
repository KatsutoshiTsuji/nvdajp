;Installer for NVDA, a free and open source screen reader for Windows
; This script requires NSIS 2.0 and above
; http://nsis.sf.net
;
; Written by Victor Tsaran, vtsaran@yahoo.com
;--------------------------------

;includes
!include "MUI2.nsh"
!include "WinMessages.nsh"
!include "Library.nsh"

;--------
;Settings

;defines for product info and paths
!define VERSION "unknown"
!define PRODUCT "NVDA"	; Don't change this for no reason, other instructions depend on this constant
!define WEBSITE "www.nvda-project.org"
!define NVDAWindowClass "wxWindowClassNR"
!define NVDAWindowTitle "NVDA"
!define NVDAApp "nvda.exe"
!define NVDATempDir "_nvda_temp_"
!define NVDASourceDir "..\source\dist"
!define SNDLogo "nvda_logo.wav"
!define INSTDIR_REG_ROOT "HKLM"
!define INSTDIR_REG_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"

;Installer flags
SetCompressor /SOLID LZMA
CRCCheck On
ShowInstDetails hide
ShowUninstDetails hide
SetOverwrite ifdiff
SetDateSave on
XPStyle on
InstProgressFlags Smooth
!define MUI_ABORTWARNING ;Should ask to exit
!define MUI_UNINSTALLER ;We want an uninstaller to be generated

;product branding
OutFile "${PRODUCT}_${VERSION}.exe"
InstallDir "$PROGRAMFILES\${PRODUCT}"
InstallDirRegKey ${INSTDIR_REG_ROOT} "${INSTDIR_REG_KEY}" "InstallDir"
Name "NVDA"
VIProductVersion "0.0.0.0" ;Needs to be here so other version info shows up
VIAddVersionKey "ProductName" "${PRODUCT}"
VIAddVersionKey "LegalCopyright" "Copyright 2006 - 2008 NVDA Contributers <http://www.nvda-project.org/>"
VIAddVersionKey "FileDescription" "NVDA installer file"
VIAddVersionKey "ProductVersion" "${VERSION}"

;set some functions as special callbacks
!define MUI_CUSTOMFUNCTION_GUIINIT NVDA_GUIInit
!define MUI_CUSTOMFUNCTION_ABORT userAbort

;--------------------------------
;Pages

;Welcome page
 !define MUI_WELCOMEPAGE_TITLE $(msg_WelcomePageTitle)
!define MUI_WELCOMEPAGE_TEXT $(msg_WelcomePageText)
!InsertMacro MUI_PAGE_WELCOME

;Licence page
!insertmacro MUI_PAGE_LICENSE "..\copying.txt"

;Page to handle previous installs
page custom pagePrevInstall

;Directory selection page
!insertmacro MUI_PAGE_DIRECTORY

;Start menu page
Var StartMenuFolder
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\${PRODUCT}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

;Installation page
!insertmacro MUI_PAGE_INSTFILES

;Install Finish page
!define MUI_FINISHPAGE_TEXT_LARGE
!define MUI_FINISHPAGE_LINK $(msg_NVDAWebSite)
!define MUI_FINISHPAGE_LINK_LOCATION ${WEBSITE}
!define MUI_FINISHPAGE_NOREBOOTSUPPORT
!insertmacro MUI_PAGE_FINISH

;Confirm uninstall page
!insertmacro MUI_UNPAGE_CONFIRM

;Uninstall page
!insertmacro MUI_UNPAGE_INSTFILES

;Uninstall finnish page
!InsertMacro MUI_UNPAGE_FINISH

;--------------------------------
 ;Language

!define UNINSTALLOG_LOCALIZE ; necessary for localization of messages from the uninstallation log file

;Include modern user interface language files
!insertmacro MUI_LANGUAGE "English" ; default language
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "TradChinese"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "Swedish"
!insertmacro MUI_LANGUAGE "Finnish"
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "Portuguese"
!insertmacro MUI_LANGUAGE "PortugueseBR"
!insertmacro MUI_LANGUAGE "Polish"
!insertmacro MUI_LANGUAGE "Czech"
!insertmacro MUI_LANGUAGE "Slovak"
!insertmacro MUI_LANGUAGE "Croatian"
!insertmacro MUI_LANGUAGE "Hungarian"
!insertmacro MUI_LANGUAGE "Galician"

;Include installer specific language strings
!include "locale\cs\langstrings.txt"
!include "locale\de\langstrings.txt"
!include "locale\en\langstrings.txt"
!include "locale\es\langstrings.txt"
!include "locale\fi\langstrings.txt"
!include "locale\fr\langstrings.txt"
!include "locale\gl\langstrings.txt"
!include "locale\hu\langstrings.txt"
!include "locale\hr\langstrings.txt"
!include "locale\it\langstrings.txt"
!include "locale\ja\langstrings.txt"
!include "locale\pl\langstrings.txt"
!include "locale\pt_pt\langstrings.txt"
!include "locale\pt_br\langstrings.txt"
!include "locale\ru\langstrings.txt"
!include "locale\se\langstrings.txt"
!include "locale\sk\langstrings.txt"
!include "locale\zh\langstrings.txt"
!include "locale\zh_tw\langstrings.txt"

;--------------------------------
;Reserve Files

ReserveFile "${NSISDIR}\Plugins\system.dll"
ReserveFile "${NSISDIR}\Plugins\banner.dll"
ReserveFile "waves\${SNDLogo}"

;-----
;Include install logger code (depends on some above settings)
!include "AdvUninstLog.nsh"
!insertmacro UNATTENDED_UNINSTALL

;-----
;Global variables

Var oldNVDAWindowHandle
 Var NVDAInstalled ;"1" if NVDA has been installed
var hmci

;-----
;Sections

;The only installable section
Section "install"
SetShellVarContext all
SetOutPath "$INSTDIR"
; open and close uninstallation log after ennumerating all the files being copied
!insertmacro UNINSTALL.LOG_OPEN_INSTALL
File /r /x lib "${NVDASourceDir}\"
CreateDirectory "$INSTDIR\lib"
!insertmacro UNINSTALL.LOG_CLOSE_INSTALL
;Unregister and remove any old ia2.dll
!define LIBRARY_COM
!insertmacro UninstallLib REGDLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\ia2.dll"
!undef LIBRARY_COM
; Install libraries
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\NVDAHelper.dll" "$INSTDIR\lib\NVDAHelper.dll" "$INSTDIR\lib"
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\keyHook.dll" "$INSTDIR\lib\keyHook.dll" "$INSTDIR\lib"
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\mouseHook.dll" "$INSTDIR\lib\mouseHook.dll" "$INSTDIR\lib"
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\virtualBuffer.dll" "$INSTDIR\lib\virtualBuffer.dll" "$INSTDIR\lib"
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\VBufBackend_gecko_ia2.dll" "$INSTDIR\lib\VBufBackend_gecko_ia2.dll" "$INSTDIR\lib"
!insertmacro InstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "${NVDASourceDir}\lib\IAccessible2Proxy.dll" "$INSTDIR\lib\IAccessible2Proxy.dll" "$INSTDIR\lib"
strcpy $NVDAInstalled "1"
;Shortcuts
!insertmacro MUI_STARTMENU_WRITE_BEGIN application
CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe" "" "$INSTDIR\${PRODUCT}.exe" 0 SW_SHOWNORMAL
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$(shortcut_readme).lnk" "$INSTDIR\documentation\$(path_readmefile)" "" "$INSTDIR\documentation\$(path_readmefile)" 0 SW_SHOWMAXIMIZED
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$(shortcut_userguide).lnk" "$INSTDIR\documentation\$(path_userguide)" "" "$INSTDIR\documentation\$(path_userguide)" 0 SW_SHOWMAXIMIZED
WriteIniStr "$INSTDIR\${PRODUCT}.url" "InternetShortcut" "URL" "${WEBSITE}"
CreateShortCut "$SMPROGRAMS\$StartMenuFolder\$(shortcut_website).lnk" "$INSTDIR\${PRODUCT}.url" "" "$INSTDIR\${PRODUCT}.url" 0
!insertmacro MUI_STARTMENU_WRITE_END
CreateShortCut "$DESKTOP\${PRODUCT}.lnk" "$INSTDIR\${PRODUCT}.exe" "" "$INSTDIR\${PRODUCT}.exe" 0 SW_SHOWNORMAL \
 CONTROL|ALT|N "Shortcut Ctrl+Alt+N"
;Items for uninstaller
CreateShortCut "$SMPROGRAMS\${PRODUCT}\$(shortcut_uninstall).lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
WriteRegStr ${INSTDIR_REG_ROOT} "${INSTDIR_REG_KEY}" "InstallDir" "$INSTDIR"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "DisplayName" "${PRODUCT} ${VERSION}"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "DisplayVersion" "${VERSION}"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "DisplayIcon" "$INSTDIR\images\nvda.ico"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "URLInfoAbout" "http://www.nvda-project.org/"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "Publisher" "nvda-project.org"
WriteRegStr ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "UninstallString" "$INSTDIR\Uninstall.exe"
WriteRegStr ${INSTDIR_REG_ROOT} "Software\${PRODUCT}" "" $INSTDIR
 SectionEnd

;The uninstall section
Section "Uninstall"
SetShellVarContext all

; Uninstall libraries
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\NVDAHelper.dll"
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\keyHook.dll"
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\mouseHook.dll"
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\virtualBuffer.dll"
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\VBufBackend_gecko_ia2.dll"
!insertmacro UninstallLib DLL NOTSHARED REBOOT_NOTPROTECTED "$INSTDIR\lib\IAccessible2Proxy.dll"

;Uninstall all files logged as being installed
!insertmacro UNINSTALL.LOG_UNINSTALL "$INSTDIR"
;end uninstall, after uninstall from all logged paths has been performed
!insertmacro UNINSTALL.LOG_END_UNINSTALL
!insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
;Cleanup shortcuts
Delete "$SMPROGRAMS\$StartMenuFolder\*.*"
RmDir "$SMPROGRAMS\$StartMenuFolder"
Delete $DESKTOP\${PRODUCT}.lnk"
Delete $INSTDIR\${PRODUCT}.url"
DeleteRegKey ${INSTDIR_REG_ROOT} "SOFTWARE\${PRODUCT}"
DeleteRegKey ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY}
Rmdir $INSTDIR
SectionEnd

;-----
;Functions

Function .onInit
; Fix an error from previous installers where the "nvda" file would be left behind after uninstall
IfFileExists "$PROGRAMFILES\NVDA" 0
Delete "$PROGRAMFILES\NVDA"
; Get the locale language ID from kernel32.dll and dynamically change language of the installer
System::Call 'kernel32::GetThreadLocale() i .r0'
StrCpy $LANGUAGE $0

;prepare log always within .onInit function
!insertmacro UNINSTALL.LOG_PREPARE_INSTALL
FunctionEnd

Function NVDA_GUIInit
Banner::show /nounload
BringToFront
InitPluginsDir
CreateDirectory $PLUGINSDIR\${NVDATempDir}
SetOutPath $PLUGINSDIR\${NVDATempDir}

;Play NVDA logo sound
File "waves\${SNDLogo}"
Push "$PLUGINSDIR\${NVDATempDir}\${SNDLogo}"
Call PlaySound

File /r "${NVDASourceDir}\"
;If NVDA is already running, kill it first before starting a new copy
call isNVDARunning
pop $1	; TRUE or FALSE
pop $oldNVDAWindowHandle
; Shut down NVDA
IntCmp $1 1 +1 Continue
MessageBox MB_OK $(msg_NVDARunning)
Continue:
IfFileExists "$APPDATA\nvda\nvda.ini" +1 +4
GetFullPathName /SHORT $0 "$APPDATA\nvda"
Exec "$PLUGINSDIR\${NVDATempDir}\${NVDAApp} -r -m -c $0"
goto Running
Exec "$PLUGINSDIR\${NVDATempDir}\${NVDAApp} -r -m"
Running:
Banner::destroy
functionEnd

function pagePrevInstall
ReadRegStr $0 ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "UninstallString"
ReadRegStr $1 ${INSTDIR_REG_ROOT} ${INSTDIR_REG_KEY} "UninstallDirectory"
Strcmp $0 "" +1 +2
abort
IfFileExists "$0" +2 +1 
abort
MessageBox MB_OK $(Msg_UninsPrev)
HideWindow
GetTempFileName $2
CopyFiles "$0" "$2"
ExecWait "$2 /S _?=$1"
delete "$2"
bringToFront
functionEnd

function manualQuitNVDA
call isNVDARunning
pop $1
pop $2
intcmp $1 1 +1 End
intcmp $2 $oldNVDAWindowHandle End +1
System::Call 'user32.dll::GetWindowThreadProcessId(i r2, *i .r3) i .r4'
System::Call 'kernel32.dll::OpenProcess(i 1048576, i 0, i r3) i .r4'
System::Call 'user32.dll::PostMessage(i r2, i ${WM_QUIT}, i 0, i 0)'
System::Call 'kernel32.dll::WaitForSingleObject(i r4, i 10000) i .r5'
end:
FunctionEnd

Function userAbort
call manualQuitNVDA
FunctionEnd

function .onInstSuccess
;create/update log always within .onInstSuccess function
!insertmacro UNINSTALL.LOG_UPDATE_INSTALL
;call manualQuitNVDA
Execwait "$PLUGINSDIR\${NVDATempDir}\${NVDAApp} -q"
Exec "$INSTDIR\${NVDAApp}"
FunctionEnd

function .oninstFailed
call manualQuitNVDA
functionEnd

Function .onGUIEnd
; Clean up the temporary folder
rmdir /R /REBOOTOK "$PLUGINSDIR\${NVDATempDir}"
FunctionEnd

; Uninstall functions
Function un.onInit
;!insertmacro MUI_UNGETLANGUAGE
; Get the locale language ID from kernel32.dll and dynamically change language of the installer
System::Call 'kernel32::GetThreadLocale() i .r0'
StrCpy $LANGUAGE $0

; Start uninstalling with a log
!insertmacro UNINSTALL.LOG_BEGIN_UNINSTALL
FunctionEnd

Function un.onUninstSuccess
HideWindow
MessageBox MB_ICONINFORMATION|MB_OK $(msg_NVDASuccessfullyRemoved)
FunctionEnd

Function isNVDARunning
FindWindow $0 "${NVDAWindowClass}" "${NVDAWindowTitle}"
;MessageBox MB_OK "Window handle is $0"
StrCmp $0 "0" +1 +3
push 0
goto end
push $0	; push the handle of NVDA window onto the stack
push 1	; push TRUE onto the stack
end:
FunctionEnd

Function PlaySound
; Retrieve the file to play
pop $9
System::Call 'msvfw32.dll::MCIWndCreate(i 0, i 0, i 0x0070, t "$9") i .r0'
StrCpy $hmci $0
; Checks format support
SendMessage $hmci 0x0490 0 0 $0
IntCmp $0 0 nosup
; if you want mci window to be hidden
ShowWindow $hmci SW_HIDE
; you can use "STR:play" or "STR:play repeat", but I saw "repeat" problems with midi files
SendMessage $hmci 0x0465 0 "STR:play"
;SendMessage $hmci ${WM_CLOSE} 0 0

nosup:
FunctionEnd

