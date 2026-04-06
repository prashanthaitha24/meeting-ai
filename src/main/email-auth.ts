import { app, safeStorage } from 'electron'
import * as fs from 'fs'
import * as path from 'path'
import * as crypto from 'crypto'
import * as bcrypt from 'bcryptjs'

interface UserRecord {
  userId: string
  email: string
  name: string
  passwordHash: string
  createdAt: number
}

function usersFilePath(): string {
  return path.join(app.getPath('userData'), 'users.enc')
}

function loadUsers(): UserRecord[] {
  try {
    const file = usersFilePath()
    if (!fs.existsSync(file)) return []
    const raw = fs.readFileSync(file)
    let json: string
    if (safeStorage.isEncryptionAvailable()) {
      json = safeStorage.decryptString(raw)
    } else {
      json = Buffer.from(raw.toString(), 'base64').toString('utf-8')
    }
    return JSON.parse(json)
  } catch {
    return []
  }
}

function saveUsers(users: UserRecord[]): void {
  const json = JSON.stringify(users)
  if (safeStorage.isEncryptionAvailable()) {
    fs.writeFileSync(usersFilePath(), safeStorage.encryptString(json))
  } else {
    fs.writeFileSync(usersFilePath(), Buffer.from(json).toString('base64'))
  }
}

export async function emailSignUp(
  email: string,
  password: string,
  name: string
): Promise<UserRecord> {
  const users = loadUsers()
  if (users.find((u) => u.email.toLowerCase() === email.toLowerCase())) {
    throw new Error('An account with this email already exists')
  }
  const passwordHash = await bcrypt.hash(password, 12)
  const user: UserRecord = {
    userId: crypto.randomUUID(),
    email: email.toLowerCase().trim(),
    name: name.trim(),
    passwordHash,
    createdAt: Date.now(),
  }
  users.push(user)
  saveUsers(users)
  return user
}

export async function emailSignIn(email: string, password: string): Promise<UserRecord> {
  const users = loadUsers()
  const user = users.find((u) => u.email.toLowerCase() === email.toLowerCase().trim())
  if (!user) throw new Error('No account found with this email')
  const valid = await bcrypt.compare(password, user.passwordHash)
  if (!valid) throw new Error('Incorrect password')
  return user
}
