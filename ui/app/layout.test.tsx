import { render, screen } from '@testing-library/react'
import RootLayout, { metadata } from './layout'

describe('RootLayout', () => {
  it('renders children correctly', () => {
    render(
      <RootLayout>
        <div data-testid="test-child">Test Content</div>
      </RootLayout>
    )

    expect(screen.getByTestId('test-child')).toBeInTheDocument()
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('has correct metadata title', () => {
    expect(metadata.title).toBe('MTG Rule Engine')
  })

  it('has correct metadata description', () => {
    expect(metadata.description).toBe('Vector-powered Magic: The Gathering rule engine and card explorer')
  })
})
