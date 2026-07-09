import { ref } from 'vue'

const progress = ref<number>(0)
const visible = ref<boolean>(false)
let timer: ReturnType<typeof setInterval> | null = null
let hideTimer: ReturnType<typeof setTimeout> | null = null

function start(): void {
  clear()
  progress.value = 0
  visible.value = true
  progress.value = 20
  timer = setInterval(() => {
    if (progress.value < 60) {
      progress.value += 15
    } else if (progress.value < 80) {
      progress.value += 5
    } else if (progress.value < 85) {
      progress.value += 2
    }
  }, 300)
}

function done(): void {
  if (timer) clearInterval(timer)
  progress.value = 100
  hideTimer = setTimeout(() => {
    visible.value = false
    progress.value = 0
  }, 400)
}

function clear(): void {
  if (timer) clearInterval(timer)
  if (hideTimer) clearTimeout(hideTimer)
  timer = null
  hideTimer = null
}

export function useProgressBar() {
  return { progress, visible, start, done }
}
