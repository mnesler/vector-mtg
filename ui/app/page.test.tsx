import { render, screen } from '@testing-library/react'
import Home from './page'

describe('Home Page', () => {
  it('renders the main heading', () => {
    render(<Home />)
    const heading = screen.getByRole('heading', { name: /MTG Rule Engine/i })
    expect(heading).toBeInTheDocument()
  })

  it('renders all three navigation cards', () => {
    render(<Home />)
    expect(screen.getByText('Card Explorer')).toBeInTheDocument()
    expect(screen.getByText('Rules Browser')).toBeInTheDocument()
    expect(screen.getByText('Deck Analyzer')).toBeInTheDocument()
  })

  it('renders Card Explorer link with correct href', () => {
    render(<Home />)
    const cardExplorerLink = screen.getByRole('link', { name: /Card Explorer/i })
    expect(cardExplorerLink).toHaveAttribute('href', '/cards')
  })

  it('renders Rules Browser link with correct href', () => {
    render(<Home />)
    const rulesBrowserLink = screen.getByRole('link', { name: /Rules Browser/i })
    expect(rulesBrowserLink).toHaveAttribute('href', '/rules')
  })

  it('renders Deck Analyzer link with correct href', () => {
    render(<Home />)
    const deckAnalyzerLink = screen.getByRole('link', { name: /Deck Analyzer/i })
    expect(deckAnalyzerLink).toHaveAttribute('href', '/deck')
  })

  it('renders the features section', () => {
    render(<Home />)
    const featuresHeading = screen.getByRole('heading', { name: /Features/i })
    expect(featuresHeading).toBeInTheDocument()
  })

  it('displays all feature items', () => {
    render(<Home />)
    expect(screen.getByText(/Vector-powered semantic search/i)).toBeInTheDocument()
    expect(screen.getByText(/Intelligent rule extraction/i)).toBeInTheDocument()
    expect(screen.getByText(/Latest printing focus/i)).toBeInTheDocument()
    expect(screen.getByText(/Card image optimization/i)).toBeInTheDocument()
    expect(screen.getByText(/Real-time API integration/i)).toBeInTheDocument()
  })

  it('renders card descriptions', () => {
    render(<Home />)
    expect(screen.getByText(/Search and browse Magic: The Gathering cards/i)).toBeInTheDocument()
    expect(screen.getByText(/Explore MTG rules and find cards/i)).toBeInTheDocument()
    expect(screen.getByText(/Analyze deck compositions/i)).toBeInTheDocument()
  })
})
