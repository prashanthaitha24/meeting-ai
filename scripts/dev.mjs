// Dev launcher — runs `electron-vite dev` with ELECTRON_RUN_AS_NODE stripped.
//
// VS Code's integrated terminal (and some IDE / extension hosts) set
// ELECTRON_RUN_AS_NODE=1. With that set, the Electron binary runs as plain
// Node: there is no GUI `app`, so GUI-only deps (@sentry/electron,
// @electron-toolkit/utils) throw the instant they load, the main process exits,
// and electron-vite restarts it — over and over. The visible symptom is the
// window "opening and closing again and again". Stripping the variable before
// we spawn the dev server fixes it regardless of where `npm run dev` is run.
import { spawn } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const env = { ...process.env }
delete env.ELECTRON_RUN_AS_NODE

const bin = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
  'node_modules',
  '.bin',
  process.platform === 'win32' ? 'electron-vite.cmd' : 'electron-vite',
)

// Sub-command defaults to `dev`; `npm start` passes `preview`.
const sub = process.argv[2] || 'dev'
const child = spawn(bin, [sub], { stdio: 'inherit', env, shell: process.platform === 'win32' })
child.on('exit', (code) => process.exit(code ?? 0))
