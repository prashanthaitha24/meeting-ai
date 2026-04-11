import { test, expect, _electron as electron } from '@playwright/test'
import path from 'path'
import fs from 'fs'
import os from 'os'

const APP_MAIN = path.resolve(__dirname, '../out/main/index.js')

// Helper — launches the built Electron app with a temp userData dir so
// each test starts completely fresh (no cached session or consent flag).
async function launchApp() {
  const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'meeting-ai-test-'))
  const app = await electron.launch({
    args: [APP_MAIN],
    env: {
      ...process.env,
      NODE_ENV: 'test',
      ELECTRON_USER_DATA: userData,
    },
  })
  return { app, userData }
}

test.beforeAll(() => {
  if (!fs.existsSync(APP_MAIN)) {
    throw new Error('App not built. Run `npm run build` before E2E tests.')
  }
})

test('app launches and shows a window', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')
    expect(await win.title()).toBeTruthy()
  } finally {
    await app.close()
    fs.rmSync(userData, { recursive: true, force: true })
  }
})

test('consent screen appears on fresh install', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')

    // Consent screen should be visible before any interaction
    await expect(win.getByText('Before You Begin')).toBeVisible({ timeout: 8000 })
    await expect(win.getByText('Accept & Continue')).toBeVisible()
    await expect(win.getByText('Decline & Quit')).toBeVisible()
  } finally {
    await app.close()
    fs.rmSync(userData, { recursive: true, force: true })
  }
})

test('accept button is disabled until checkbox is checked', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')
    await win.waitForSelector('text=Before You Begin')

    const acceptBtn = win.getByText('Accept & Continue')
    await expect(acceptBtn).toBeDisabled()

    await win.getByRole('checkbox').click()
    await expect(acceptBtn).toBeEnabled()
  } finally {
    await app.close()
    fs.rmSync(userData, { recursive: true, force: true })
  }
})

test('accepting consent shows auth screen', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')
    await win.waitForSelector('text=Before You Begin')

    await win.getByRole('checkbox').click()
    await win.getByText('Accept & Continue').click()

    // After consent, should show auth screen
    await expect(win.getByText(/Sign in|Log in|Welcome/i)).toBeVisible({ timeout: 5000 })
  } finally {
    await app.close()
    fs.rmSync(userData, { recursive: true, force: true })
  }
})

test('declining consent closes the app', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')
    await win.waitForSelector('text=Before You Begin')

    await win.getByText('Decline & Quit').click()

    // App should close within a few seconds
    await app.waitForEvent('close', { timeout: 5000 })
  } finally {
    fs.rmSync(userData, { recursive: true, force: true })
  }
})

test('window is always on top and visible', async () => {
  const { app, userData } = await launchApp()
  try {
    const win = await app.firstWindow()
    await win.waitForLoadState('domcontentloaded')

    const isAlwaysOnTop = await app.evaluate(({ BrowserWindow }) => {
      return BrowserWindow.getAllWindows()[0]?.isAlwaysOnTop() ?? false
    })
    expect(isAlwaysOnTop).toBe(true)
  } finally {
    await app.close()
    fs.rmSync(userData, { recursive: true, force: true })
  }
})
