import { searchCards, getSimilarCards, getCardsForRule, getAllRules } from './api'

global.fetch = jest.fn()

describe('API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('searchCards', () => {
    it('calls the correct endpoint with default parameters', async () => {
      const mockResponse = {
        search_term: 'Lightning Bolt',
        count: 1,
        cards: [],
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await searchCards('Lightning Bolt')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Lightning+Bolt&limit=50&include_nonplayable=false'
      )
      expect(result).toEqual(mockResponse)
    })

    it('calls with custom limit and includeNonplayable parameters', async () => {
      const mockResponse = { search_term: 'Test', count: 0, cards: [] }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await searchCards('Test', 100, true)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/cards/search?name=Test&limit=100&include_nonplayable=true'
      )
    })

    it('throws error when response is not ok', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
      })

      await expect(searchCards('Test')).rejects.toThrow('Search failed: Not Found')
    })
  })

  describe('getSimilarCards', () => {
    it('calls the correct endpoint with default parameters', async () => {
      const mockResponse = {
        card_id: '123',
        card_name: 'Test Card',
        count: 0,
        similar_cards: [],
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await getSimilarCards('123')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/cards/123/similar?limit=20&include_nonplayable=false'
      )
      expect(result).toEqual(mockResponse)
    })

    it('includes rule_filter when provided', async () => {
      const mockResponse = {
        card_id: '123',
        card_name: 'Test Card',
        rule_filter: 'flying',
        count: 0,
        similar_cards: [],
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await getSimilarCards('123', 20, 'flying', true)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/cards/123/similar?limit=20&include_nonplayable=true&rule_filter=flying'
      )
    })

    it('throws error when response is not ok', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Server Error',
      })

      await expect(getSimilarCards('123')).rejects.toThrow('Failed to get similar cards: Server Error')
    })
  })

  describe('getCardsForRule', () => {
    it('calls the correct endpoint with default parameters', async () => {
      const mockResponse = {
        rule_name: 'flying',
        count: 0,
        cards: [],
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await getCardsForRule('flying')

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/rules/flying/cards?limit=50&include_nonplayable=false'
      )
      expect(result).toEqual(mockResponse)
    })

    it('calls with custom parameters', async () => {
      const mockResponse = { rule_name: 'haste', count: 0, cards: [] }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      await getCardsForRule('haste', 30, true)

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/rules/haste/cards?limit=30&include_nonplayable=true'
      )
    })

    it('throws error when response is not ok', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      })

      await expect(getCardsForRule('test')).rejects.toThrow('Failed to get cards for rule: Bad Request')
    })
  })

  describe('getAllRules', () => {
    it('calls the correct endpoint', async () => {
      const mockResponse = {
        rules: [
          { id: 1, rule_name: 'flying', rule_text: 'This creature can only be blocked by creatures with flying or reach' },
          { id: 2, rule_name: 'haste', rule_text: 'This creature can attack and tap immediately' },
        ],
      }

      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await getAllRules()

      expect(global.fetch).toHaveBeenCalledWith('/api/rules')
      expect(result).toEqual(mockResponse)
    })

    it('throws error when response is not ok', async () => {
      ;(global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      })

      await expect(getAllRules()).rejects.toThrow('Failed to get rules: Internal Server Error')
    })
  })
})
