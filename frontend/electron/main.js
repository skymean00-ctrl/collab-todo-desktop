const { app, BrowserWindow, Tray, Menu, nativeImage, Notification, ipcMain, dialog } = require('electron')
const { autoUpdater } = require('electron-updater')
const path = require('path')
const { getServerUrl, setServerUrl } = require('./config')

const isDev = process.env.NODE_ENV === 'development'

let mainWindow = null
let tray = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 900,
    minHeight: 600,
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

function createTray() {
  const iconPath = path.join(__dirname, '../public/tray-icon.png')
  let icon = nativeImage.createFromPath(iconPath)
  if (icon.isEmpty()) icon = nativeImage.createEmpty()
  tray = new Tray(icon)

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'CollabTodo 열기',
      click: () => { mainWindow.show(); mainWindow.focus() },
    },
    { type: 'separator' },
    {
      label: '종료',
      click: () => { app.isQuitting = true; app.quit() },
    },
  ])

  tray.setToolTip('CollabTodo')
  tray.setContextMenu(contextMenu)
  tray.on('double-click', () => { mainWindow.show(); mainWindow.focus() })
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

// 자동 업데이트 설치
ipcMain.on('install-update', () => autoUpdater.quitAndInstall())

// ── 앱 초기화 ────────────────────────────────────────────

app.whenReady().then(() => {
  createWindow()
  createTray()

  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify()
  }
})

app.on('window-all-closed', () => {
  // 트레이로 유지 (종료하지 않음)
})

app.on('activate', () => {
  if (mainWindow) mainWindow.show()
})

// 자동 업데이트 이벤트
autoUpdater.on('update-available', () => {
  mainWindow?.webContents.send('update-available')
})
autoUpdater.on('update-downloaded', () => {
  mainWindow?.webContents.send('update-downloaded')
})
