; Inno Setup script for KONEKTA

#define MyAppName "KONEKTA"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PSHS-ZRC Student Proponents"
#define MyAppExeName "KONEKTA.exe"

[Setup]
AppId={{D9A0C925-DC53-4D4A-8D0A-71F412556851}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/
DefaultDirName={localappdata}\Programs\KONEKTA
DefaultGroupName=KONEKTA
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\installer_output
OutputBaseFilename=KONEKTA-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\KONEKTA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "_internal\resources\images\Sunnyside_World_ASSET_PACK_V2.1\Sunnyside_World_Gamemaker\*,_internal\resources\images\__MACOSX\*"
Source: "..\open_konekta_data_folder.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\reset_konekta_data.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\KONEKTA"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\KONEKTA"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{autoprograms}\KONEKTA\Open Data Folder"; Filename: "{app}\open_konekta_data_folder.bat"
Name: "{autoprograms}\KONEKTA\Reset Local Data"; Filename: "{app}\reset_konekta_data.bat"
Name: "{autoprograms}\KONEKTA\Uninstall KONEKTA"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch KONEKTA"; Flags: nowait postinstall skipifsilent
