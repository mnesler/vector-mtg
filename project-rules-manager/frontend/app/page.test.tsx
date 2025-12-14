import { render, screen } from '@testing-library/react'
import Home from './page'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

describe('Home Page', () => {
  it('renders the search bar', () => {
    render(<Home />)
    const searchInput = screen.getByRole('searchbox', { name: /Search cards/i })
    expect(searchInput).toBeInTheDocument()
  })

  it('renders the results table', () => {
    render(<Home />)
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('renders table headers', () => {
    render(<Home />)
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Type')).toBeInTheDocument()
    expect(screen.getByText('Cost')).toBeInTheDocument()
    expect(screen.getByText('Text')).toBeInTheDocument()
  })

  it('shows placeholder message when no results', () => {
    render(<Home />)
    expect(screen.getByText(/Use the search bar, Max/i)).toBeInTheDocument()
  })

  it('renders semantic and keyword search buttons', () => {
    render(<Home />)
    expect(screen.getByRole('button', { name: /Semantic search/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Keyword search/i })).toBeInTheDocument()
  })
})
