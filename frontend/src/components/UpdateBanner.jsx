import { useState, useEffect } from 'react'

export default function UpdateBanner() {
  const [state, setState] = useState(null) // null | 'available' | 'downloading' | 'ready'

  useEffect(() => {
    if (!window.electronAPI) return
    window.electronAPI.onUpdateAvailable(() => setState('available'))
    window.electronAPI.onUpdateDownloaded(() => setState('ready'))
  }, [])

  if (!state) return null

  return (
    <div className="bg-blue-600 text-white px-4 py-2 flex items-center justify-between text-sm z-50">
      {state === 'available' && (
        <>
          <span>🆕 새 버전이 있습니다.</span>
          <button
            onClick={() => { setState('downloading'); window.electronAPI.downloadUpdate() }}
            className="ml-4 bg-white text-blue-700 px-3 py-1 rounded font-medium hover:bg-blue-50"
          >
            다운로드
          </button>
        </>
      )}
      {state === 'downloading' && (
        <span>⏬ 업데이트 다운로드 중...</span>
      )}
      {state === 'ready' && (
        <>
          <span>✅ 업데이트 준비 완료. 지금 설치하시겠습니까?</span>
          <button
            onClick={() => window.electronAPI.installUpdate()}
            className="ml-4 bg-white text-blue-700 px-3 py-1 rounded font-medium hover:bg-blue-50"
          >
            지금 설치 및 재시작
          </button>
        </>
      )}
    </div>
  )
}
