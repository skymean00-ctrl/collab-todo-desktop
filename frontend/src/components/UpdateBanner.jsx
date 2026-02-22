import { useState, useEffect } from 'react'

export default function UpdateBanner() {
  const [updateReady, setUpdateReady] = useState(false)

  useEffect(() => {
    if (!window.electronAPI) return
    window.electronAPI.onUpdateDownloaded(() => setUpdateReady(true))
  }, [])

  if (!updateReady) return null

  return (
    <div className="bg-green-600 text-white px-4 py-2 flex items-center justify-between text-sm z-50">
      <span>새 버전이 다운로드 되었습니다. 지금 설치하시겠습니까?</span>
      <button
        onClick={() => window.electronAPI.installUpdate()}
        className="ml-4 bg-white text-green-700 px-3 py-1 rounded font-medium hover:bg-green-50"
      >
        지금 설치 및 재시작
      </button>
    </div>
  )
}
