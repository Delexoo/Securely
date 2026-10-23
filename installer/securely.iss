#define MyAppName "Securely"
#ifndef MyAppVersion
#define MyAppVersion "0.1.10"
#endif
#define MyAppPublisher "Delexoo"
#define MyAppURL "https://trysecurely.vercel.app"
#define MyAppExeName "SecurelyShell.exe"

[Setup]
AppId={{A7C3E91B-4F2D-4A18-9E6C-8B1D5F0A3C27}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases.html
AppCopyright=Copyright (C) 2026 Delexoo
DefaultDirName={autopf}\Delexoo\Securely
DefaultGroupName=Securely
DisableProgramGroupPage=yes
LicenseFile=license.rtf
SetupIconFile=..\securely-app\host\securely.ico
UninstallDisplayIcon={app}\SecurelyShell.exe
; Securely shield logo (replaces default package/CD wizard art)
WizardSmallImageFile=wizard\wizard-small-58.png,wizard\wizard-small-147.png,wizard\wizard-small-256.png
WizardImageFile=wizard\wizard-202x386.png,wizard\wizard-240x459.png
WizardImageBackColor=clWhite
WizardSmallImageBackColor=clWhite
WizardImageAlphaFormat=defined
WizardImageStretch=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UsedUserAreasWarning=no
OutputDir=..\dist-setup
OutputBaseFilename=Securely-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayName=Securely
VersionInfoCompany=Delexoo
VersionInfoProductName=Securely
VersionInfoVersion={#MyAppVersion}.0
VersionInfoCopyright=Copyright (C) 2026 Delexoo
SetupLogging=yes
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startonlogon"; Description: "Start Securely when I sign in to Windows"; GroupDescription: "Shortcuts:"; Flags: unchecked

#ifndef Payload
#define Payload "stage"
#endif

[Files]
Source: "..\dist-setup\{#Payload}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Securely"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Comment: "Securely screen threat monitor"
Name: "{group}\Securely website"; Filename: "{#MyAppURL}"
Name: "{group}\Uninstall Securely"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Securely"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Securely"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startonlogon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Securely"; Flags: nowait postinstall skipifsilent
