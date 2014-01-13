#define MyAppName "Kindle Comic Converter"
#define MyAppVersion "3.7"
#define MyAppPublisher "Ciro Mattia Gonano, Paweł Jastrzębski"
#define MyAppURL "http://kcc.vulturis.eu/"
#define MyAppExeName "KCC.exe"

[Setup]
AppId={{7D279A59-C65E-4DA7-B165-56DD06596216}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2012-2013 Ciro Mattia Gonano and Paweł Jastrzębski
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputBaseFilename=KindleComicConverter_win_{#MyAppVersion}
SetupIconFile=icons\comic2ebook.ico
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ShowLanguageDialog=no
LanguageDetectionMethod=none
WizardImageFile=icons\Wizard.bmp
WizardSmallImageFile=icons\Wizard-Small.bmp
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesAssociations=True
InfoAfterFile=other\InstallWarning.rtf
SignTool=SignTool /d $q{#MyAppName}$q /du $q{#MyAppURL}$q $f

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "CBZassociation"; Description: "CBZ"; GroupDescription: "File associations:"
Name: "CBRassociation"; Description: "CBR"; GroupDescription: "File associations:"
Name: "CB7association"; Description: "CB7"; GroupDescription: "File associations:"

[Files]
; x64 files
Source: "build\exe.win-amd64-2.7\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\LIBEAY32.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\library.zip"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\PIL._imaging.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\PIL._imagingft.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\PyQt4.QtCore.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\PyQt4.QtGui.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\PyQt4.QtNetwork.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\python27.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\QtCore4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\QtGui4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\QtNetwork4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\select.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\sip.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\SSLEAY32.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "build\exe.win-amd64-2.7\_psutil_mswindows.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: Is64BitInstallMode
Source: "other\vcredist_x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Check: Is64BitInstallMode
; x86 files
Source: "build\exe.win32-2.7\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion solidbreak; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_ctypes.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_hashlib.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_multiprocessing.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_socket.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_ssl.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\bz2.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\LIBEAY32.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\library.zip"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\PIL._imaging.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\PIL._imagingft.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\pyexpat.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\PyQt4.QtCore.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\PyQt4.QtGui.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\PyQt4.QtNetwork.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\python27.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\QtCore4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\QtGui4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\QtNetwork4.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\select.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\sip.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\SSLEAY32.dll"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\unicodedata.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "build\exe.win32-2.7\_psutil_mswindows.pyd"; DestDir: "{app}"; Flags: ignoreversion; Check: not Is64BitInstallMode
Source: "other\vcredist_x86.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall; Check: not Is64BitInstallMode
; Common files
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion solidbreak
Source: "other\Additional-LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "other\UnRAR.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "other\7za.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Readme"; Filename: "https://github.com/ciromattia/kcc#kcc"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{tmp}\vcredist_x64.exe"; Parameters: "/passive /Q:a /c:""msiexec /qb /i vcredist.msi"" "; StatusMsg: "Installing Microsoft Visual C++ 2008 Redistributable Package..."; Check: Is64BitInstallMode
Filename: "{tmp}\vcredist_x86.exe"; Parameters: "/passive /Q:a /c:""msiexec /qb /i vcredist.msi"" "; StatusMsg: "Installing Microsoft Visual C++ 2008 Redistributable Package..."; Check: not Is64BitInstallMode

[Messages]
WelcomeLabel1=Welcome to the KCC Setup Wizard
FinishedHeadingLabel=Completing the KCC Setup Wizard

[Registry]
Root: HKCR; SubKey: ".cbz"; ValueType: string; ValueData: "KCCZIP"; Flags: uninsdeletekey; Tasks: CBZassociation
Root: HKCR; SubKey: "KCCZIP"; ValueType: string; ValueData: "KCC ZIP Archive"; Flags: uninsdeletekey; Tasks: CBZassociation
Root: HKCR; SubKey: "KCCZIP\Shell\Open\Command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: CBZassociation
Root: HKCR; Subkey: "KCCZIP\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletevalue; Tasks: CBZassociation
Root: HKCR; SubKey: ".cbr"; ValueType: string; ValueData: "KCCRAR"; Flags: uninsdeletekey; Tasks: CBRassociation
Root: HKCR; SubKey: "KCCRAR"; ValueType: string; ValueData: "KCC RAR Archive"; Flags: uninsdeletekey; Tasks: CBRassociation
Root: HKCR; SubKey: "KCCRAR\Shell\Open\Command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: CBRassociation
Root: HKCR; Subkey: "KCCRAR\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletevalue; Tasks: CBRassociation
Root: HKCR; SubKey: ".cb7"; ValueType: string; ValueData: "KCCCB7"; Flags: uninsdeletekey; Tasks: CB7association
Root: HKCR; SubKey: "KCCCB7"; ValueType: string; ValueData: "KCC 7z Archive"; Flags: uninsdeletekey; Tasks: CB7association
Root: HKCR; SubKey: "KCCCB7\Shell\Open\Command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey; Tasks: CB7association
Root: HKCR; Subkey: "KCCCB7\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Flags: uninsdeletevalue; Tasks: CB7association
