; Inno Setup Script for Collab Todo Desktop
; Windows 설치 프로그램 생성 스크립트
; 모든 의존성이 포함된 독립 실행형 설치 파일 생성

#define AppName "Collab Todo Desktop"
#define AppVersion "1.0.0"
#define AppPublisher "Collab Todo Team"
#define AppURL "https://github.com/your-org/collab-todo-desktop"
#define AppExeName "CollabToDoDesktop.exe"
#define BuildDir "dist"
#define OutputDir "installer"

[Setup]
; 설치 프로그램 기본 정보
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
AllowRootDirectory=no
DisableDirPage=no
DisableProgramGroupPage=no
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir={#OutputDir}
OutputBaseFilename=CollabTodoDesktop-Setup-{#AppVersion}
SetupIconFile=
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64
; 설치 시 관리자 권한 불필요 (사용자 디렉토리에 설치 가능)
; 모든 의존성이 포함되어 있으므로 추가 설치 불필요
; 사용자가 설치 위치를 선택할 수 있도록 설정

; 한국어 지원
[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[DirPage]
; 설치 위치 선택 페이지 설정
DirExistsWarning=auto
; 사용자가 설치 위치를 변경할 수 있도록 허용

[Files]
; PyInstaller로 빌드된 실행 파일 및 모든 의존성
; PyInstaller가 Python 런타임과 모든 라이브러리를 포함하므로
; 사용자가 Python을 별도로 설치할 필요가 없습니다.
Source: "{#BuildDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; 설정 파일 템플릿 (있는 경우)
Source: "config\*.example"; DestDir: "{app}\config"; Flags: ignoreversion; Check: DirExists(ExpandConstant('{src}\config'))

; 문서 파일 (있는 경우)
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs; Check: DirExists(ExpandConstant('{src}\docs')) 

[Icons]
; 시작 메뉴 바로가기
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; 바탕화면 바로가기 (선택적)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; 빠른 실행 바로가기 (Windows 7 이하)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon

[Run]
; 설치 후 실행 옵션 (선택적)
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// 설치 전 검사: 필요한 Windows 버전 확인
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Windows 7 이상 지원 (Windows 10 이상 권장)
  // PyInstaller로 빌드된 실행 파일은 Python 런타임을 포함하므로
  // 사용자가 Python을 별도로 설치할 필요가 없습니다.
end;

// 설치 위치 유효성 검사
function NextButtonClick(CurPageID: Integer): Boolean;
var
  Dir: String;
begin
  Result := True;
  
  // 설치 위치 선택 페이지에서 유효성 검사
  if CurPageID = wpSelectDir then
  begin
    Dir := WizardForm.DirEdit.Text;
    
    // 빈 경로 확인
    if Trim(Dir) = '' then
    begin
      MsgBox('설치 위치를 선택하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
    
    // 최소 경로 길이 확인
    if Length(Trim(Dir)) < 3 then
    begin
      MsgBox('유효한 설치 경로를 입력하세요.', mbError, MB_OK);
      Result := False;
      Exit;
    end;
  end;
end;

// 설치 완료 후 처리
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 설치 완료
    // 선택적으로 설치 위치를 표시할 수 있음
  end;
end;

