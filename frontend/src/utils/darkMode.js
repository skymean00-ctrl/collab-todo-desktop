export function initDarkMode() {
  const saved = localStorage.getItem('darkMode')
  if (saved === 'dark') {
    document.documentElement.classList.add('dark')
  } else if (saved === 'light') {
    document.documentElement.classList.remove('dark')
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark')
  }
}

export function toggleDarkMode() {
  const isDark = document.documentElement.classList.toggle('dark')
  localStorage.setItem('darkMode', isDark ? 'dark' : 'light')
  return isDark
}

export function isDark() {
  return document.documentElement.classList.contains('dark')
}
