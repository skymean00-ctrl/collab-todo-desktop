const { app, BrowserWindow, Tray, Menu, nativeImage, Notification, ipcMain, dialog } = require('electron')
const { autoUpdater } = require('electron-updater')
const path = require('path')
const { getServerUrl, setServerUrl } = require('./config')
const { version } = require('../package.json')

const isDev = process.env.NODE_ENV === 'development'

// ── 싱글 인스턴스 보장 (트레이 아이콘 중복 생성 방지) ──────────────────────
// 두 번째 인스턴스가 실행되면 즉시 종료하고, 기존 창을 앞으로 가져옴
if (!app.requestSingleInstanceLock()) {
  app.quit()
  process.exit(0)
}

app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.show()
    mainWindow.focus()
  }
})

// 기본 메뉴바 완전 제거
Menu.setApplicationMenu(null)

// Windows 알림/작업표시줄 앱 ID 설정
app.setAppUserModelId('com.company.collabtodo')

let mainWindow = null
let tray = null
let updateState = 'idle' // 'idle' | 'checking' | 'available' | 'downloading' | 'downloaded' | 'error'
let isManualUpdateCheck = false // 트레이에서 직접 누른 경우에만 "최신 버전" 다이얼로그 표시

// 아이콘 경로 (개발/프로덕션 공통)
function getIconPath(filename) {
  return path.join(__dirname, '../public', filename)
}

function createWindow() {
  const iconPath = getIconPath('icon.ico')
  const icon = nativeImage.createFromPath(iconPath)

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: `CollabTodo v${version}`,
    icon: icon.isEmpty() ? undefined : icon,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    show: false,
  })

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
  })

  // 닫기 버튼 → 트레이로 숨김
  mainWindow.on('close', (event) => {
    if (!app.isQuitting) {
      event.preventDefault()
      mainWindow.hide()
    }
  })
}

function rebuildTrayMenu() {
  if (!tray) return

  const updateLabels = {
    idle:        '업데이트 확인',
    checking:    '확인 중...',
    available:   '업데이트 다운로드',
    downloading: '다운로드 중...',
    downloaded:  '재시작하여 설치',
    error:       '업데이트 오류 (재시도)',
  }
  const updateEnabled = !['checking', 'downloading'].includes(updateState)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: `CollabTodo v${version} 열기`,
      click: () => { mainWindow.show(); mainWindow.focus() },
    },
    { type: 'separator' },
    {
      label: updateLabels[updateState] || '업데이트 확인',
      enabled: updateEnabled,
      click: () => {
        if (updateState === 'idle' || updateState === 'error') {
          isManualUpdateCheck = true
          updateState = 'checking'
          rebuildTrayMenu()
          autoUpdater.checkForUpdates().catch(() => {
            isManualUpdateCheck = false
            updateState = 'error'
            rebuildTrayMenu()
            dialog.showMessageBox(mainWindow, {
              type: 'error',
              title: '업데이트 오류',
              message: '업데이트 서버에 연결할 수 없습니다.',
            })
          })
        } else if (updateState === 'available') {
          updateState = 'downloading'
          rebuildTrayMenu()
          autoUpdater.downloadUpdate()
        } else if (updateState === 'downloaded') {
          autoUpdater.quitAndInstall()
        }
      },
    },
    { type: 'separator' },
    {
      label: '종료',
      click: () => { app.isQuitting = true; app.quit() },
    },
  ])

  tray.setContextMenu(contextMenu)
}

function createTray() {
  const iconPath = getIconPath('tray-icon.png')
  let icon = nativeImage.createFromPath(iconPath)
  // 트레이 아이콘은 16x16이 최적
  if (!icon.isEmpty()) {
    icon = icon.resize({ width: 16, height: 16 })
  }
  tray = new Tray(icon)
  tray.setToolTip(`CollabTodo v${version}`)
  tray.on('double-click', () => { mainWindow.show(); mainWindow.focus() })
  rebuildTrayMenu()
}

// ── IPC 핸들러 ──────────────────────────────────────────

// 저장된 서버 URL 반환
ipcMain.handle('get-server-url', () => getServerUrl())

// 서버 URL 저장
ipcMain.handle('set-server-url', (_, url) => {
  setServerUrl(url)
  return true
})

// 데스크톱 푸시 알림
ipcMain.on('show-notification', (_, { title, body, taskId }) => {
  if (Notification.isSupported()) {
    const notif = new Notification({ title, body })
    notif.on('click', () => {
      mainWindow.show()
      mainWindow.focus()
      if (taskId) mainWindow.webContents.send('navigate-to-task', taskId)
    })
    notif.show()
  }
})

// 파일 다운로드 (저장 위치 선택 다이얼로그)
ipcMain.handle('download-file', async (_, { url, filename, token }) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: filename,
    filters: [{ name: 'All Files', extensions: ['*'] }],
  })
  if (result.canceled) return { canceled: true }

  const https = require('https')
  const http = require('http')
  const fs = require('fs')

  return new Promise((resolve) => {
    const urlObj = new URL(url)
    const protocol = urlObj.protocol === 'https:' ? https : http
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      headers: { Authorization: `Bearer ${token}` },
    }
    const file = fs.createWriteStream(result.filePath)
    protocol.get(options, (res) => {
      res.pipe(file)
      file.on('finish', () => { file.close(); resolve({ success: true, filePath: result.filePath }) })
    }).on('error', (err) => resolve({ success: false, error: err.message }))
  })
})

// 자동 업데이트 다운로드 시작
ipcMain.on('download-update', () => autoUpdater.downloadUpdate())

// 자동 업데이트 설치
ipcMain.on('install-update', () => autoUpdater.quitAndInstall())

// ── 앱 초기화 ────────────────────────────────────────────

app.whenReady().then(() => {
  createWindow()
  createTray()

  if (!isDev) {
    autoUpdater.autoDownload = false
    // 시작 시 조용히 체크 (최신 버전이어도 다이얼로그 없음)
    autoUpdater.checkForUpdates().catch(() => {})
  }
})

app.on('window-all-closed', () => {
  // 트레이로 유지 (종료하지 않음)
})

app.on('activate', () => {
  if (mainWindow) mainWindow.show()
})

// 자동 업데이트 이벤트
autoUpdater.on('error', () => {
  updateState = 'error'
  rebuildTrayMenu()
})
autoUpdater.on('update-not-available', () => {
  updateState = 'idle'
  rebuildTrayMenu()
  // 사용자가 직접 트레이에서 클릭한 경우에만 다이얼로그 표시
  if (isManualUpdateCheck && mainWindow) {
    isManualUpdateCheck = false
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: '최신 버전',
      message: `현재 버전(v${version})이 최신 버전입니다.`,
    })
  }
})
autoUpdater.on('update-available', () => {
  updateState = 'available'
  rebuildTrayMenu()
  mainWindow?.webContents.send('update-available')
})
autoUpdater.on('download-progress', (progress) => {
  const pct = Math.round(progress.percent || 0)
  if (tray) tray.setToolTip(`CollabTodo - 다운로드 ${pct}%`)
})
autoUpdater.on('update-downloaded', () => {
  updateState = 'downloaded'
  rebuildTrayMenu()
  if (tray) tray.setToolTip(`CollabTodo v${version} - 업데이트 준비 완료`)
  mainWindow?.webContents.send('update-downloaded')
})
