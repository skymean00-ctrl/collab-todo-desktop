; Inno Setup Script for Collab Todo Desktop
; Windows 설치 프로그램 생성 스크립트
; 모든 의존성이 포함된 독립 실행형 설치 파일 생성
; Python, MySQL 클라이언트 등 모든 런타임이 내장되어 있어
; 사용자가 별도의 개발환경을 설치할 필요가 없습니다.

#define AppName "Collab Todo Desktop"
#define AppVersion "1.0.0"
#define AppPublisher "Collab Todo Team"
#define AppURL "https://github.com/skymean00-ctrl/collab-todo-desktop"
#define AppExeName "CollabToDoDesktop.exe"
#define BuildDir "dist"
#define OutputDir "installer"

[Setup]
AppId={{A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
DisableDirPage=no
DisableProgramGroupPage=no
OutputDir={#OutputDir}
OutputBaseFilename=CollabTodoDesktop-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
; 관리자 권한 불필요 - 사용자 폴더에도 설치 가능
; 모든 의존성(Python 런타임 포함)이 내장되어 추가 설치 불필요

; 한국어 우선, 영어 지원
[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; PyInstaller로 빌드된 독립 실행 파일 (Python 런타임 + 모든 라이브러리 포함)
Source: "{#BuildDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; 설정 파일 템플릿 (선택적)
Source: "config\*.example"; DestDir: "{app}\config"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; 시작 메뉴 바로가기
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; 바탕화면 바로가기 (기본 체크됨)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; 빠른 실행 바로가기 (Windows 7 이하)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
; 설치 완료 후 바로 실행 옵션
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 제거 시 앱 데이터 정리
Type: filesandordirs; Name: "{app}\config"
Type: filesandordirs; Name: "{app}\logs"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Dir: String;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    Dir := WizardForm.DirEdit.Text;
    if Trim(Dir) = '' then
    begin
      MsgBox('설치 위치를 선택하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    if Length(Trim(Dir)) < 3 then
    begin
      MsgBox('유효한 설치 경로를 입력하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;
