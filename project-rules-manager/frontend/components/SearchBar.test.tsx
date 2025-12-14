import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBar from './SearchBar'

// Mock fetch globally
global.fetch = jest.fn()

describe('SearchBar Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.runOnlyPendingTimers()
    jest.useRealTimers()
  })

  it('renders search input', () => {
    render(<SearchBar />)
    const input = screen.getByRole('searchbox')
    expect(input).toBeInTheDocument()
  })

  it('renders with custom placeholder', () => {
    render(<SearchBar placeholder="Find cards..." />)
    const input = screen.getByPlaceholderText('Find cards...')
    expect(input).toBeInTheDocument()
  })

  it('renders semantic search button', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button', { name: /Semantic search/i })
    expect(button).toBeInTheDocument()
  })

  it('renders keyword search button', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button', { name: /Keyword search/i })
    expect(button).toBeInTheDocument()
  })

  it('starts in semantic mode', () => {
    render(<SearchBar />)
    const semanticBtn = screen.getByRole('button', { name: /Semantic search/i })
    expect(semanticBtn).toHaveClass('variant-filled-primary')
  })

  it('switches to keyword mode when keyword button clicked', () => {
    render(<SearchBar />)
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })

    fireEvent.click(keywordBtn)

    expect(keywordBtn).toHaveClass('variant-filled-primary')
  })

  it('switches back to semantic mode when semantic button clicked', () => {
    render(<SearchBar />)
    const semanticBtn = screen.getByRole('button', { name: /Semantic search/i })
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })

    fireEvent.click(keywordBtn)
    expect(keywordBtn).toHaveClass('variant-filled-primary')

    fireEvent.click(semanticBtn)
    expect(semanticBtn).toHaveClass('variant-filled-primary')
  })

  it('allows typing in search input', async () => {
    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)
    const input = screen.getByRole('searchbox') as HTMLInputElement

    await user.type(input, 'lightning')

    expect(input.value).toBe('lightning')
  })

  it('calls keyword search endpoint with correct query', async () => {
    const mockResponse = {
      query: 'lightning',
      search_type: 'keyword',
      count: 1,
      cards: [{ id: '123', name: 'Lightning Bolt' }]
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const onSearchResults = jest.fn()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)

    // Switch to keyword mode
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'lightning')
    jest.advanceTimersByTime(300) // Trigger debounce

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/cards/keyword?query=lightning&limit=10'
      )
    })
  })

  it('calls semantic search endpoint when in semantic mode', async () => {
    const mockResponse = {
      query: 'red damage',
      search_type: 'semantic',
      count: 1,
      cards: [{ id: '456', name: 'Shock' }]
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    })

    const onSearchResults = jest.fn()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)

    // Already in semantic mode by default
    const input = screen.getByRole('searchbox')
    await user.type(input, 'red damage{Enter}')

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/cards/semantic?query=red%20damage&limit=10'
      )
    })
  })

  it('debounces search requests in keyword mode', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
    })

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)

    // Switch to keyword mode for auto-search
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'abc')

    // Should not call fetch yet
    expect(global.fetch).not.toHaveBeenCalled()

    // Advance timers by debounce delay
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      // Should only call once after debounce
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })
  })

  it('calls onSearchResults callback with results', async () => {
    const mockCards = [
      { id: '123', name: 'Lightning Bolt' },
      { id: '456', name: 'Shock' }
    ]

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        query: 'lightning',
        search_type: 'keyword',
        count: 2,
        cards: mockCards
      })
    })

    const onSearchResults = jest.fn()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)

    // Switch to keyword mode
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'lightning')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith(mockCards, 'lightning', 'keyword', false)
    })
  })

  it('clears results when input is cleared', async () => {
    const onSearchResults = jest.fn()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)
    const input = screen.getByRole('searchbox')

    await user.type(input, 'test')
    await user.clear(input)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([], '', 'semantic', false)
    })
  })

  it('handles search errors gracefully', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const onSearchResults = jest.fn()
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)

    // Switch to keyword mode for auto-search
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([], 'test', 'keyword', false)
      expect(consoleErrorSpy).toHaveBeenCalled()
    })

    consoleErrorSpy.mockRestore()
  })

  it('handles non-ok HTTP responses', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error'
    })

    const onSearchResults = jest.fn()
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)

    // Switch to keyword mode for auto-search
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox')
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([], 'test', 'keyword', false)
    })

    consoleErrorSpy.mockRestore()
  })

  it('shows loading state during search', async () => {
    ;(global.fetch as jest.Mock).mockImplementation(
      () =>
        new Promise(resolve =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
              }),
            1000
          )
        )
    )

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)

    // Switch to keyword mode for auto-search
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox') as HTMLInputElement
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(input.disabled).toBe(true)
    })
  })

  it('disables input during search', async () => {
    let resolveSearch: (value: any) => void
    const searchPromise = new Promise(resolve => {
      resolveSearch = resolve
    })

    ;(global.fetch as jest.Mock).mockReturnValueOnce(searchPromise)

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)

    // Switch to keyword mode for auto-search
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)

    const input = screen.getByRole('searchbox') as HTMLInputElement
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(input.disabled).toBe(true)
    })

    // Resolve the search
    resolveSearch!({
      ok: true,
      json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
    })

    await waitFor(() => {
      expect(input.disabled).toBe(false)
    })
  })

  it('auto-searches in keyword mode but not in semantic mode', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
    })

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)

    // Start in semantic mode - no auto-search
    const input = screen.getByRole('searchbox')
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    // Should not auto-search in semantic mode
    expect(global.fetch).not.toHaveBeenCalled()

    // Switch to keyword mode
    const keywordBtn = screen.getByRole('button', { name: /Keyword search/i })
    fireEvent.click(keywordBtn)
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      // Should auto-search in keyword mode
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/cards/keyword')
      )
    })
  })
})
