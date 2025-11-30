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

  it('renders mode toggle button', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button', { name: /Switch to/i })
    expect(button).toBeInTheDocument()
  })

  it('starts in keyword mode', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button')
    expect(button).toHaveTextContent('Keyword')
  })

  it('toggles to semantic mode when button clicked', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button')

    fireEvent.click(button)

    expect(button).toHaveTextContent('Semantic')
  })

  it('toggles back to keyword mode', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button')

    fireEvent.click(button)
    expect(button).toHaveTextContent('Semantic')

    fireEvent.click(button)
    expect(button).toHaveTextContent('Keyword')
  })

  it('displays keyword mode description', () => {
    render(<SearchBar />)
    expect(screen.getByText(/Exact text matching/i)).toBeInTheDocument()
  })

  it('displays semantic mode description after toggle', () => {
    render(<SearchBar />)
    const button = screen.getByRole('button')

    fireEvent.click(button)

    expect(screen.getByText(/Natural language search/i)).toBeInTheDocument()
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

    // Toggle to semantic mode
    const button = screen.getByRole('button')
    fireEvent.click(button)

    // Type query
    const input = screen.getByRole('searchbox')
    await user.type(input, 'red damage')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/cards/semantic?query=red%20damage&limit=10'
      )
    })
  })

  it('debounces search requests', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
    })

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)
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
    const input = screen.getByRole('searchbox')

    await user.type(input, 'lightning')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith(mockCards)
    })
  })

  it('clears results when input is cleared', async () => {
    const onSearchResults = jest.fn()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)
    const input = screen.getByRole('searchbox')

    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await user.clear(input)
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([])
    })
  })

  it('handles search errors gracefully', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    const onSearchResults = jest.fn()
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()
    const user = userEvent.setup({ delay: null })
    render(<SearchBar onSearchResults={onSearchResults} />)
    const input = screen.getByRole('searchbox')

    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([])
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
    const input = screen.getByRole('searchbox')

    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(onSearchResults).toHaveBeenCalledWith([])
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

  it('re-searches when mode is toggled', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ query: '', search_type: 'keyword', count: 0, cards: [] })
    })

    const user = userEvent.setup({ delay: null })
    render(<SearchBar />)
    const input = screen.getByRole('searchbox')
    const button = screen.getByRole('button')

    // Type a query
    await user.type(input, 'test')
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1)
    })

    // Toggle mode
    fireEvent.click(button)
    jest.advanceTimersByTime(300)

    await waitFor(() => {
      // Should trigger a new search with semantic endpoint
      expect(global.fetch).toHaveBeenCalledTimes(2)
      expect(global.fetch).toHaveBeenLastCalledWith(
        expect.stringContaining('/api/cards/semantic')
      )
    })
  })
})
