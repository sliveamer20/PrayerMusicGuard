; Inno Setup script for صلاة وسكون (PrayerMusicGuard)
; Installs the prebuilt PyInstaller executable as a normal Windows application.

#define MyAppName "PrayerMusicGuard"
#define MyAppNameAr "صلاة وسكون"
#define MyAppVersion "1.2.7"
#define MyAppExeName "PrayerMusicGuard.exe"
#define MyAppDirName "PrayerMusicGuard"

[Setup]
AppId={{B7C4A5D1-9E2F-4C3A-8D61-7F0E5A9C2B41}
AppName={#MyAppNameAr}
AppVersion={#MyAppVersion}
AppVerName={#MyAppNameAr} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppNameAr}
UninstallDisplayName={#MyAppNameAr}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=dist
OutputBaseFilename=PrayerMusicGuard-Setup
SetupIconFile=assets\icons\prayer_music_guard.ico
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "arabic"; MessagesFile: "compiler:Languages\Arabic.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\PrayerMusicGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppNameAr}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppNameAr}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppNameAr}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Remove the app's own per-user autostart Run entry ONLY on uninstall.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PrayerMusicGuard"; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppNameAr}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Inno removes {app} files automatically; these lines also clear empty dirs
; and the WebView2 user-data cache created at runtime under %APPDATA%.
Type: dirifempty; Name: "{app}"
Type: filesandordirs; Name: "{userappdata}\PrayerMusicGuard\webview2_data"

[Code]
{---------------------------------------------------------------------------
  Stale-uninstall cleanup. If the uninstall registry entry for THIS app still
  exists but its uninstaller binary is gone (e.g. the app folder was deleted
  manually), remove the stale key so a reinstall never reports "already
  installed". Scoped strictly to this app's AppId; never touches anything else.
---------------------------------------------------------------------------}
const
  UninstallBase = 'Software\Microsoft\Windows\CurrentVersion\Uninstall';
  AppIdKey = 'B7C4A5D1-9E2F-4C3A-8D61-7F0E5A9C2B41';

procedure RemoveStaleUninstallKeys();
var
  KeyPath: string;
  UninstallString: string;
  AppExe: string;
  IsStale: Boolean;
begin
  KeyPath := UninstallBase + '\' + AppIdKey + '_is1';
  IsStale := False;
  if RegKeyExists(HKEY_LOCAL_MACHINE_64, KeyPath) or RegKeyExists(HKEY_LOCAL_MACHINE_32, KeyPath) or RegKeyExists(HKEY_CURRENT_USER, KeyPath) then
  begin
    IsStale := True;
    if RegQueryStringValue(HKEY_LOCAL_MACHINE_64, KeyPath, 'UninstallString', UninstallString) or
       RegQueryStringValue(HKEY_LOCAL_MACHINE_32, KeyPath, 'UninstallString', UninstallString) or
       RegQueryStringValue(HKEY_CURRENT_USER, KeyPath, 'UninstallString', UninstallString) then
    begin
      if RegQueryStringValue(HKEY_LOCAL_MACHINE_64, KeyPath, 'DisplayIcon', AppExe) or
         RegQueryStringValue(HKEY_LOCAL_MACHINE_32, KeyPath, 'DisplayIcon', AppExe) or
         RegQueryStringValue(HKEY_CURRENT_USER, KeyPath, 'DisplayIcon', AppExe) then
        IsStale := not FileExists(AppExe)
      else
        IsStale := False;
    end;
  end;

  if IsStale then
  begin
    if RegKeyExists(HKEY_LOCAL_MACHINE_64, KeyPath) then
      RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE_64, KeyPath);
    if RegKeyExists(HKEY_LOCAL_MACHINE_32, KeyPath) then
      RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE_32, KeyPath);
    if RegKeyExists(HKEY_CURRENT_USER, KeyPath) then
      RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, KeyPath);
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  RemoveStaleUninstallKeys();
end;
