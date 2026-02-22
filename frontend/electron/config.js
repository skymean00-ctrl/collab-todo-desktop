const fs = require('fs')
const path = require('path')
const { app } = require('electron')

const CONFIG_PATH = path.join(app.getPath('userData'), 'config.json')

function getConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'))
  } catch {
    return {}
  }
}

function setConfig(data) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(data, null, 2), 'utf8')
}

function getServerUrl() {
  return getConfig().serverUrl || null
}

function setServerUrl(url) {
  const config = getConfig()
  config.serverUrl = url
  setConfig(config)
}

module.exports = { getConfig, setConfig, getServerUrl, setServerUrl }
