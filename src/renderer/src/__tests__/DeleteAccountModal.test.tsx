import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

// Import inline — DeleteAccountModal is defined in App.tsx, so we replicate it here
// Once it's extracted to its own file, import from '../components/DeleteAccountModal'
import React, { useState } from 'react'

function DeleteAccountModal({ onClose, onDeleted }: { onClose: () => void; onDeleted: () => void }) {
  const [status, setStatus] = useState<'idle' | 'deleting' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const handleDelete = async () => {
    setStatus('deleting')
    try {
      const ok = await window.api.deleteAccount()
      if (ok) { onDeleted() } else {
        setErrorMsg('Deletion failed. Please contact support@thavionai.com')
        setStatus('error')
      }
    } catch (e: unknown) {
      setErrorMsg(e instanceof Error ? e.message : 'An error occurred')
      setStatus('error')
    }
  }

  return (
    <div>
      <h2>Delete Account</h2>
      <p>This action is permanent and cannot be undone</p>
      {status === 'error' && <p data-testid="error">{errorMsg}</p>}
      <button onClick={onClose} disabled={status === 'deleting'}>Cancel</button>
      <button onClick={handleDelete} disabled={status === 'deleting'} data-testid="confirm-delete">
        {status === 'deleting' ? 'Deleting…' : 'Delete My Account'}
      </button>
    </div>
  )
}

describe('DeleteAccountModal', () => {
  const onClose = vi.fn()
  const onDeleted = vi.fn()

  beforeEach(() => {
    onClose.mockClear()
    onDeleted.mockClear()
    vi.mocked(window.api.deleteAccount).mockReset().mockResolvedValue(true)
  })

  it('renders confirmation warning', () => {
    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)
    expect(screen.getByText(/permanent and cannot be undone/)).toBeInTheDocument()
  })

  it('calls onDeleted after successful deletion', async () => {
    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)

    fireEvent.click(screen.getByTestId('confirm-delete'))

    await waitFor(() => {
      expect(window.api.deleteAccount).toHaveBeenCalledOnce()
      expect(onDeleted).toHaveBeenCalledOnce()
    })
  })

  it('shows error when deletion fails', async () => {
    vi.mocked(window.api.deleteAccount).mockResolvedValue(false)

    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)
    fireEvent.click(screen.getByTestId('confirm-delete'))

    await waitFor(() => {
      expect(screen.getByTestId('error')).toBeInTheDocument()
      expect(onDeleted).not.toHaveBeenCalled()
    })
  })

  it('shows error when API throws', async () => {
    vi.mocked(window.api.deleteAccount).mockRejectedValue(new Error('Server error'))

    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)
    fireEvent.click(screen.getByTestId('confirm-delete'))

    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument()
    })
  })

  it('calls onClose when cancel is clicked', () => {
    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)

    fireEvent.click(screen.getByText('Cancel'))

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('disables buttons while deleting', async () => {
    let resolve: (v: boolean) => void
    vi.mocked(window.api.deleteAccount).mockImplementation(() => new Promise(r => { resolve = r }))

    render(<DeleteAccountModal onClose={onClose} onDeleted={onDeleted} />)
    fireEvent.click(screen.getByTestId('confirm-delete'))

    await waitFor(() => {
      expect(screen.getByTestId('confirm-delete')).toBeDisabled()
      expect(screen.getByText('Cancel')).toBeDisabled()
    })

    resolve!(true)
  })
})
