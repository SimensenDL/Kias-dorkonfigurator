; Inno Setup script for KIAS Dørkonfigurator
; Genererer Windows-installasjonsprogram
;
; Forutsetninger:
;   - PyInstaller har bygd applikasjonen til dist\KIAS Dørkonfigurator\
;   - Inno Setup 6 er installert
;
; Bygg med:
;   iscc installer\kias_installer.iss

#define MyAppName "KIAS Dørkonfigurator"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Kvanne Industrier AS"
#define MyAppURL "https://kvanne.no"
#define MyAppExeName "KIAS Dørkonfigurator.exe"
#define MyAppAssocName "KIAS Dørprosjekt"
#define MyAppAssocExt ".kdf"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{1B675A06-7074-40CA-BBFE-2892579FB3BB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=KIAS-Dorkonfigurator-{#MyAppVersion}-Setup
SetupIconFile=..\assets\KIAS-dorer-logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0
ChangesAssociations=yes
ShowLanguageDialog=no

[Languages]
Name: "norwegian"; MessagesFile: "compiler:Languages\Norwegian.isl"

[Tasks]
Name: "desktopicon"; Description: "Opprett snarvei på &skrivebordet"; GroupDescription: "Ekstra snarveier:"

[Files]
Source: "..\dist\KIAS Dørkonfigurator\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
; Filassosiasjon for .kdf-filer
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocExt}\OpenWithProgids"; ValueType: string; ValueName: "{#MyAppAssocKey}"; ValueData: ""; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}"; ValueType: string; ValueName: ""; ValueData: "{#MyAppAssocName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\{#MyAppAssocKey}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".kdf"; ValueData: ""

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Start {#MyAppName}"; Flags: nowait postinstall skipifsilent
