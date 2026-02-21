; CollabTodo 커스텀 NSIS 스크립트
; 설치 완료 후 앱 자동 실행

!macro customInstall
  ; 설치 완료 메시지 (한국어)
  MessageBox MB_OK "CollabTodo가 설치되었습니다.$\n$\n처음 실행 시 서버 주소를 입력해주세요."
!macroend
