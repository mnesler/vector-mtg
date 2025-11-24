/**
 * Deck analyzer page logic
 */

let categoryPieChart = null;
let currentAnalysis = null;

const exampleDecks = {
    aggro: `Lightning Bolt
Monastery Swiftspear
Goblin Guide
Lava Spike
Rift Bolt
Skullcrack
Eidolon of the Great Revel
Searing Blaze`,

    control: `Counterspell
Mana Leak
Opt
Brainstorm
Supreme Verdict
Wrath of God
Fact or Fiction
Cryptic Command`,

    ramp: `Sol Ring
Mana Crypt
Birds of Paradise
Llanowar Elves
Kodama's Reach
Cultivate
Explosive Vegetation
Ranger's Path`
};

function parseDeckList(text) {
    const lines = text.split('\n').filter(line => line.trim());
    const cardNames = [];

    lines.forEach(line => {
        // Remove quantity if present (e.g., "4 Lightning Bolt" -> "Lightning Bolt")
        const match = line.match(/^\d+\s+(.+)$/) || line.match(/^(.+)$/);
        if (match && match[1]) {
            cardNames.push(match[1].trim());
        }
    });

    return cardNames;
}

async function analyzeDeck() {
    const input = document.getElementById('deckInput').value.trim();

    if (!input) {
        alert('Please enter a deck list');
        return;
    }

    const cardNames = parseDeckList(input);

    if (cardNames.length === 0) {
        alert('No valid cards found in deck list');
        return;
    }

    // Show loading
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('loadingState').classList.remove('hidden');

    try {
        const analysis = await api.analyzeDeck(cardNames);
        currentAnalysis = analysis;

        renderAnalysis(analysis);
    } catch (error) {
        console.error('Deck analysis failed:', error);
        alert('Failed to analyze deck. Make sure the API is running and card names are correct.');
        document.getElementById('loadingState').classList.add('hidden');
        document.getElementById('emptyState').classList.remove('hidden');
    }
}

function renderAnalysis(analysis) {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    // Summary
    document.getElementById('totalCards').textContent = formatNumber(analysis.deck_size);
    document.getElementById('cardsFound').textContent = formatNumber(analysis.cards_found);
    document.getElementById('cardsWithRules').textContent = formatNumber(analysis.cards_with_rules);
    document.getElementById('uniqueRules').textContent = formatNumber(analysis.rule_distribution?.length || 0);

    // Category pie chart
    if (analysis.category_summary && analysis.category_summary.length > 0) {
        renderCategoryChart(analysis.category_summary);
    }

    // Top rules list
    if (analysis.rule_distribution && analysis.rule_distribution.length > 0) {
        renderTopRules(analysis.rule_distribution);
    }
}

function renderCategoryChart(categories) {
    const canvas = document.getElementById('categoryPieChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    if (categoryPieChart) {
        categoryPieChart.destroy();
    }

    const sortedCategories = categories.sort((a, b) => b.unique_cards - a.unique_cards);

    categoryPieChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: sortedCategories.map(c => c.category || 'Uncategorized'),
            datasets: [{
                data: sortedCategories.map(c => c.unique_cards),
                backgroundColor: sortedCategories.map(c => getCategoryColor(c.category)),
                borderColor: '#1f2937',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#9ca3af',
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} cards (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

function renderTopRules(rules) {
    const container = document.getElementById('topRulesList');

    const topRules = rules.sort((a, b) => b.card_count - a.card_count).slice(0, 10);

    container.innerHTML = topRules.map(rule => {
        const categoryColor = getCategoryColor(rule.category);

        return `
            <div class="flex items-center justify-between p-3 bg-gray-900 rounded hover:bg-gray-800 transition-colors">
                <div class="flex-1">
                    <div class="flex items-center gap-2">
                        <span class="font-semibold text-white">${rule.rule_name.replace(/_/g, ' ')}</span>
                        <span class="text-xs px-2 py-0.5 rounded font-semibold"
                              style="background-color: ${categoryColor}33; color: ${categoryColor}">
                            ${rule.category || 'Uncategorized'}
                        </span>
                    </div>
                    ${rule.cards && rule.cards.length > 0 ? `
                        <p class="text-xs text-gray-500 mt-1">
                            ${rule.cards.slice(0, 3).join(', ')}${rule.cards.length > 3 ? '...' : ''}
                        </p>
                    ` : ''}
                </div>
                <div class="text-right">
                    <p class="font-mono font-semibold text-white">${rule.card_count}</p>
                    <p class="text-xs text-gray-400">card${rule.card_count !== 1 ? 's' : ''}</p>
                </div>
            </div>
        `;
    }).join('');
}

function clearDeck() {
    document.getElementById('deckInput').value = '';
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');

    if (categoryPieChart) {
        categoryPieChart.destroy();
        categoryPieChart = null;
    }
}

function loadExample(deckType) {
    if (exampleDecks[deckType]) {
        document.getElementById('deckInput').value = exampleDecks[deckType];
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Nothing to load on init
});
