; PingMonitor Pro v2.0 - Inno Setup Script
; Professional Windows Installer like Node.js
; Requires Inno Setup 6.x (https://jrsoftware.org/isinfo.php)

#define MyAppName "PingMonitor Pro"
#define MyAppVersion "2.3"
#define MyAppPublisher "Fabrizio Cerchia"
#define MyAppURL "https://github.com/fabriziocer/pingmonitor"
#define MyAppExeName "PingMonitorPro.pyw"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{E8A9F2C1-4D3B-4E5F-9A1C-8B7D6E5F4A3B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\dist
OutputBaseFilename=PingMonitorPro_v2.3_Setup
SetupIconFile=..\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\icon.ico
DisableProgramGroupPage=yes
DisableWelcomePage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "startupicon"; Description: "Launch PingMonitor Pro at Windows startup"; GroupDescription: "Additional options:"; Flags: unchecked

[Files]
; Main application files
Source: "..\PingMonitorPro.pyw"; DestDir: "{app}"; Flags: ignoreversion
; Source: "..\START.bat"; DestDir: "{app}"; Flags: ignoreversion  - REMOVED (not needed with installer)
Source: "..\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\icon.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "..\GUIDA_INSTALLAZIONE_PROFESSIONALE.txt"; DestDir: "{app}"; Flags: ignoreversion - REMOVED (file deleted)
; Source: "..\FIX_FINALE_EMAIL_E_INSTALLAZIONE.txt"; DestDir: "{app}"; Flags: ignoreversion - REMOVED (file deleted)

; Source code
Source: "..\src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

; Config folder
Source: "..\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python launcher script
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\icon.ico"; Comment: "Launch PingMonitor Pro"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon; Comment: "Launch PingMonitor Pro"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\icon.ico"; Tasks: quicklaunchicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\launcher.bat"; IconFilename: "{app}\icon.ico"; Tasks: startupicon

[Registry]
; Add to Windows Firewall exceptions (optional)
Root: HKLM; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Run]
; Install Python dependencies during setup
Filename: "pythonw"; Parameters: "-m pip install --upgrade pip"; StatusMsg: "Upgrading pip..."; Flags: runhidden
Filename: "pythonw"; Parameters: "-m pip install PyQt6 requests paramiko cryptography SQLAlchemy loguru rich Pillow icmplib openpyxl matplotlib"; StatusMsg: "Installing dependencies..."; Flags: runhidden

; Offer to launch application after installation
Filename: "{app}\launcher.bat"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  PythonPath: String;
  DependencyPage: TOutputProgressWizardPage;

function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  // Check if Python is installed and in PATH
  Result := (Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or
             Exec('pythonw', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)) and
            (ResultCode = 0);
end;

function GetPythonPath: String;
var
  TempFile: String;
  Lines: TArrayOfString;
  ResultCode: Integer;
begin
  Result := '';

  // Try to get Python path
  TempFile := ExpandConstant('{tmp}\pythonpath.txt');
  if Exec('cmd.exe', '/c python -c "import sys; print(sys.executable)" > "' + TempFile + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if LoadStringsFromFile(TempFile, Lines) then
    begin
      if GetArrayLength(Lines) > 0 then
        Result := Trim(Lines[0]);
    end;
  end;
end;

procedure InitializeWizard;
begin
  // Create a custom page for dependency installation
  DependencyPage := CreateOutputProgressPage('Installing Dependencies', 'Please wait while Setup installs Python dependencies...');
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ErrorCode: Integer;
begin
  Result := True;

  if CurPageID = wpReady then
  begin
    // Check for Python before installation
    if not IsPythonInstalled then
    begin
      if MsgBox('Python is not detected on your system. PingMonitor Pro requires Python 3.8 or later.' + #13#10#13#10 +
                'Would you like to open the Python download page?' + #13#10#13#10 +
                'After installing Python, please run this installer again.',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOW, ewNoWait, ErrorCode);
      end;
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    DependencyPage.SetText('Installing Python dependencies...', 'This may take a few minutes.');
    DependencyPage.Show;

    try
      // Install dependencies
      DependencyPage.SetProgress(0, 100);
      DependencyPage.SetText('Installing dependencies...', 'Upgrading pip...');
      Exec('pythonw', '-m pip install --upgrade pip', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(20, 100);
      DependencyPage.SetText('Installing dependencies...', 'Installing PyQt6...');
      Exec('pythonw', '-m pip install PyQt6', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(40, 100);
      DependencyPage.SetText('Installing dependencies...', 'Installing network libraries...');
      Exec('pythonw', '-m pip install requests paramiko', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(60, 100);
      DependencyPage.SetText('Installing dependencies...', 'Installing security libraries...');
      Exec('pythonw', '-m pip install cryptography SQLAlchemy', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(80, 100);
      DependencyPage.SetText('Installing dependencies...', 'Installing utility libraries...');
      Exec('pythonw', '-m pip install loguru rich Pillow icmplib', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(90, 100);
      DependencyPage.SetText('Installing dependencies...', 'Installing Excel and Chart libraries...');
      Exec('pythonw', '-m pip install openpyxl matplotlib', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

      DependencyPage.SetProgress(100, 100);
      DependencyPage.SetText('Installation complete!', 'All dependencies installed successfully.');

    finally
      DependencyPage.Hide;
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\src\__pycache__"
Type: filesandordirs; Name: "{app}\*.log"
Type: filesandordirs; Name: "{app}\*.db"
