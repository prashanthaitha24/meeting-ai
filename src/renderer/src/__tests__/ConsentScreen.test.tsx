import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ConsentScreen } from '../components/ConsentScreen'

describe('ConsentScreen', () => {
  const onAccept = vi.fn()
  const onDecline = vi.fn()

  beforeEach(() => {
    onAccept.mockClear()
    onDecline.mockClear()
  })

  it('renders terms and accept button disabled by default', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    expect(screen.getByText('Accept & Continue')).toBeDisabled()
    expect(screen.getByText('Decline & Quit')).toBeEnabled()
  })

  it('enables accept button after checking the checkbox', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    const checkbox = screen.getByRole('checkbox')
    fireEvent.click(checkbox)

    expect(screen.getByText('Accept & Continue')).toBeEnabled()
  })

  it('calls onAccept when accepted', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(screen.getByText('Accept & Continue'))

    expect(onAccept).toHaveBeenCalledOnce()
    expect(onDecline).not.toHaveBeenCalled()
  })

  it('calls onDecline when declined', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    fireEvent.click(screen.getByText('Decline & Quit'))

    expect(onDecline).toHaveBeenCalledOnce()
    expect(onAccept).not.toHaveBeenCalled()
  })

  it('shows required data processor disclosures', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    expect(screen.getByText(/OpenAI Whisper/)).toBeInTheDocument()
    expect(screen.getByText(/Anthropic Claude/)).toBeInTheDocument()
    expect(screen.getByText(/Supabase/)).toBeInTheDocument()
    expect(screen.getByText(/Stripe/)).toBeInTheDocument()
  })

  it('does not call onAccept if checkbox not checked', () => {
    render(<ConsentScreen onAccept={onAccept} onDecline={onDecline} />)

    // Accept button is disabled, clicking shouldn't fire
    const acceptBtn = screen.getByText('Accept & Continue')
    fireEvent.click(acceptBtn)

    expect(onAccept).not.toHaveBeenCalled()
  })
})
