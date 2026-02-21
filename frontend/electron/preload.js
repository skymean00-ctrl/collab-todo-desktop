const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  // 데스크톱 알림
  showNotification: (data) => ipcRenderer.send('show-notification', data),

  // 파일 다운로드 (저장 위치 선택 다이얼로그 포함)
  downloadFile: (data) => ipcRenderer.invoke('download-file', data),

  // 자동 업데이트
  onUpdateAvailable: (cb) => ipcRenderer.on('update-available', cb),
  onUpdateDownloaded: (cb) => ipcRenderer.on('update-downloaded', cb),
  installUpdate: () => ipcRenderer.send('install-update'),

  // 업무 페이지 이동 (알림 클릭 시)
  onNavigateToTask: (cb) => ipcRenderer.on('navigate-to-task', (_, taskId) => cb(taskId)),
})
