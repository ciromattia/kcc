#define MyAppName "Kindle Comic Converter"
#define MyAppVersion "5.2.1"
#define MyAppPublisher "Ciro Mattia Gonano, Paweł Jastrzębski"
#define MyAppURL "http://kcc.iosphe.re/"
#define MyAppExeName "KCC.exe"

[Setup]
AppId={{7D279A59-C65E-4DA7-B165-56DD06596216}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=Copyright (C) 2012-2016 Ciro Mattia Gonano and Paweł Jastrzębski
ArchitecturesAllowed=x64 
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
OutputBaseFilename=KindleComicConverter_win_{#MyAppVersion}
SetupIconFile=icons\comic2ebook.ico
SolidCompression=yes
ShowLanguageDialog=no
LanguageDetectionMethod=none
WizardImageFile=icons\Wizard.bmp
WizardSmallImageFile=icons\Wizard-Small.bmp
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesAssociations=True
InfoAfterFile=other\windows\InstallWarning.rtf
SignTool=SignTool /d $q{#MyAppName}$q /du $q{#MyAppURL}$q $f
MinVersion=0,6.0
OutputDir=dist
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "CBZassociation"; Description: "CBZ"; GroupDescription: "File associations:"
Name: "CBRassociation"; Description: "CBR"; GroupDescription: "File associations:"
Name: "CB7association"; Description: "CB7"; GroupDescription: "File associations:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion solidbreak
Source: "other\windows\Additional-LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "other\windows\UnRAR.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "other\windows\7za.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "other\windows\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: ignoreversion deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Readme"; Filename: "https://github.com/ciromattia/kcc#kcc"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /passive /norestart"; StatusMsg: "Installing Microsoft Visual C++ 2015 Redistributable Package..."
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall

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

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;