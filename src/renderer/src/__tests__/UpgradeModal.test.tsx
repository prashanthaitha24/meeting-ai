import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UpgradeModal } from '../components/UpgradeModal'

describe('UpgradeModal', () => {
  const onClose = vi.fn()

  beforeEach(() => {
    onClose.mockClear()
    vi.mocked(window.api.stripeCheckout).mockReset().mockResolvedValue(undefined)
    vi.mocked(window.api.onStripeCancel).mockReturnValue(() => {})
  })

  it('defaults to yearly plan', () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)
    // Yearly button should be active (has bg-white/10 class via selected state)
    const yearlyBtn = screen.getByText('Yearly')
    expect(yearlyBtn).toBeInTheDocument()
    // CTA shows yearly price
    expect(screen.getByText(/\$49\.99 \/ year/)).toBeInTheDocument()
  })

  it('switches to monthly plan', () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    fireEvent.click(screen.getByText('Monthly'))

    expect(screen.getByText(/\$9\.99 \/ month/)).toBeInTheDocument()
  })

  it('calls stripeCheckout with yearly when yearly is selected', async () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    fireEvent.click(screen.getByText(/Get Pro/))

    await waitFor(() => {
      expect(window.api.stripeCheckout).toHaveBeenCalledWith('yearly')
    })
  })

  it('calls stripeCheckout with monthly when monthly is selected', async () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    fireEvent.click(screen.getByText('Monthly'))
    fireEvent.click(screen.getByText(/Get Pro/))

    await waitFor(() => {
      expect(window.api.stripeCheckout).toHaveBeenCalledWith('monthly')
    })
  })

  it('shows opened state after successful checkout launch', async () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    fireEvent.click(screen.getByText(/Get Pro/))

    await waitFor(() => {
      expect(screen.getByText(/Checkout opened in your browser/)).toBeInTheDocument()
    })
  })

  it('shows error when checkout fails', async () => {
    vi.mocked(window.api.stripeCheckout).mockRejectedValue(new Error('Network error'))

    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)
    fireEvent.click(screen.getByText(/Get Pro/))

    await waitFor(() => {
      expect(screen.getByText(/Could not open checkout/)).toBeInTheDocument()
    })
  })

  it('calls onClose when Maybe later is clicked', () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    fireEvent.click(screen.getByText('Maybe later'))

    expect(onClose).toHaveBeenCalledOnce()
  })

  it('shows savings percentage badge on yearly option', () => {
    render(<UpgradeModal onClose={onClose} freeCallsUsed={3} />)

    expect(screen.getByText(/SAVE \d+%/)).toBeInTheDocument()
  })
})
