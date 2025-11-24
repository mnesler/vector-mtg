/**
 * MTG Rule Engine API Client
 * Handles all communication with the backend API
 */

class MTGRuleEngineAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Statistics
    async getStats() {
        return this.request('/api/stats');
    }

    async getRuleStats() {
        return this.request('/api/stats/rules');
    }

    // Cards
    async searchCard(name) {
        return this.request(`/api/cards/search?name=${encodeURIComponent(name)}`);
    }

    async getCardsByRule(ruleName, limit = 50) {
        return this.request(`/api/cards/search?rule=${ruleName}&limit=${limit}`);
    }

    async getCard(cardId) {
        return this.request(`/api/cards/${cardId}`);
    }

    async getSimilarCards(cardId, limit = 20, ruleFilter = null) {
        let url = `/api/cards/${cardId}/similar?limit=${limit}`;
        if (ruleFilter) {
            url += `&rule_filter=${encodeURIComponent(ruleFilter)}`;
        }
        return this.request(url);
    }

    // Rules
    async listRules(category = null, limit = 100) {
        let url = `/api/rules?limit=${limit}`;
        if (category) {
            url += `&category=${encodeURIComponent(category)}`;
        }
        return this.request(url);
    }

    async getRuleCards(ruleName, limit = 50) {
        return this.request(`/api/rules/${ruleName}/cards?limit=${limit}`);
    }

    async getCategories() {
        return this.request('/api/categories');
    }

    // Analysis
    async analyzeDeck(cardNames) {
        return this.request('/api/analyze/deck', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ cards: cardNames })
        });
    }

    // Health check
    async healthCheck() {
        return this.request('/health');
    }
}

// Create global API instance
const api = new MTGRuleEngineAPI();

// Utility functions
function formatNumber(num) {
    return num.toLocaleString();
}

function formatPercentage(value, total) {
    return ((value / total) * 100).toFixed(1) + '%';
}

function getCategoryColor(category) {
    const colors = {
        'Removal': '#ef4444',
        'Creature Removal': '#dc2626',
        'Permanent Removal': '#f87171',
        'Card Draw': '#3b82f6',
        'Mana Production': '#10b981',
        'Evasion': '#8b5cf6',
        'Token Generation': '#f59e0b',
        'Life Manipulation': '#ec4899',
        'Counterspells': '#06b6d4',
        'Tutors': '#a855f7',
        'Graveyard Recursion': '#6366f1',
        'Exile Effects': '#84cc16',
        'Protection': '#14b8a6',
        'Combat Tricks': '#f97316',
        'Triggered Abilities': '#eab308',
        'Activated Abilities': '#22c55e'
    };
    return colors[category] || '#6b7280';
}

function truncate(str, maxLength) {
    if (!str) return '';
    return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
}
