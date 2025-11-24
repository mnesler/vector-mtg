/**
 * Cards page logic
 */

let currentResults = [];

async function init() {
    // Load rules for dropdown
    await loadRuleFilter();

    // Check for URL params
    const urlParams = new URLSearchParams(window.location.search);
    const searchQuery = urlParams.get('search');
    if (searchQuery) {
        document.getElementById('cardNameSearch').value = searchQuery;
        await searchByName();
    }
}

async function loadRuleFilter() {
    const select = document.getElementById('ruleFilter');

    // Add loading option
    select.innerHTML = '<option value="">Loading rules...</option>';
    select.disabled = true;

    try {
        const rules = await api.listRules();

        // Clear loading
        select.innerHTML = '<option value="">Select a rule...</option>';
        select.disabled = false;

        const sortedRules = rules.rules.sort((a, b) => b.card_count - a.card_count);

        sortedRules.forEach(rule => {
            const option = document.createElement('option');
            option.value = rule.rule_name;
            option.textContent = `${rule.rule_name.replace(/_/g, ' ')} (${formatNumber(rule.card_count)})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Failed to load rules:', error);
        select.innerHTML = '<option value="">Error loading rules</option>';
        select.disabled = false;
    }
}

async function searchByName() {
    const searchInput = document.getElementById('cardNameSearch');
    const query = searchInput.value.trim();

    if (!query) {
        alert('Please enter a card name');
        return;
    }

    showLoading();

    try {
        const result = await api.searchCard(query);

        if (result.rules) {
            // Single card result
            currentResults = [result];
        } else {
            currentResults = [];
        }

        renderResults(`Search: "${query}"`, currentResults.length);
    } catch (error) {
        console.error('Search failed:', error);
        showError('Card not found or API error');
    }
}

async function searchByRule() {
    const select = document.getElementById('ruleFilter');
    const ruleName = select.value;

    if (!ruleName) {
        alert('Please select a rule');
        return;
    }

    showLoading();

    try {
        const result = await api.getCardsByRule(ruleName, 20);
        currentResults = result.cards || [];

        const selectedText = select.options[select.selectedIndex].text;
        renderResults(`Rule: ${selectedText}`, currentResults.length);
    } catch (error) {
        console.error('Filter failed:', error);
        showError('Failed to load cards');
    }
}

function renderResults(title, count) {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    document.getElementById('resultsTitle').textContent = title;
    document.getElementById('resultsCount').textContent = `${count} result${count !== 1 ? 's' : ''}`;

    const grid = document.getElementById('cardGrid');

    if (currentResults.length === 0) {
        grid.innerHTML = '<div class="col-span-3 text-center py-8 text-gray-400">No cards found</div>';
        return;
    }

    grid.innerHTML = currentResults.map(card => renderCardCard(card)).join('');
}

function renderCardCard(card) {
    const rules = card.rules || [];
    const hasRules = rules.length > 0;

    return `
        <div class="bg-gray-800 rounded-lg p-5 border border-gray-700 hover:border-blue-500 transition-colors">
            <div class="mb-3">
                <h3 class="text-lg font-bold text-white">${card.name}</h3>
                <div class="flex items-center gap-2 mt-1">
                    ${card.mana_cost ? `<span class="text-sm font-mono text-blue-300">${card.mana_cost}</span>` : ''}
                    ${card.cmc ? `<span class="text-xs text-gray-500">CMC ${card.cmc}</span>` : ''}
                </div>
            </div>

            <p class="text-sm text-gray-400 mb-3">${card.type_line}</p>

            ${card.oracle_text ? `
                <p class="text-sm text-gray-300 mb-4 line-clamp-3">
                    ${card.oracle_text}
                </p>
            ` : ''}

            ${hasRules ? `
                <div class="mb-3">
                    <p class="text-xs text-gray-500 mb-2">Matched Rules:</p>
                    <div class="flex flex-wrap gap-1">
                        ${rules.slice(0, 3).map(rule => `
                            <span class="inline-block px-2 py-1 rounded text-xs font-semibold"
                                  style="background-color: ${getCategoryColor(rule.category_name)}33; color: ${getCategoryColor(rule.category_name)}">
                                ${rule.rule_name.replace(/_/g, ' ')}
                            </span>
                        `).join('')}
                        ${rules.length > 3 ? `<span class="text-xs text-gray-500 self-center">+${rules.length - 3} more</span>` : ''}
                    </div>
                </div>
            ` : ''}

            ${card.keywords && card.keywords.length > 0 ? `
                <div class="text-xs text-gray-500">
                    Keywords: ${card.keywords.slice(0, 3).join(', ')}${card.keywords.length > 3 ? '...' : ''}
                </div>
            ` : ''}
        </div>
    `;
}

function showLoading() {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('loadingState').classList.remove('hidden');
}

function showError(message) {
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('emptyState').classList.remove('hidden');

    document.getElementById('emptyState').innerHTML = `
        <svg class="mx-auto h-24 w-24 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 class="mt-4 text-xl font-semibold text-gray-400">Error</h3>
        <p class="mt-2 text-gray-500">${message}</p>
    `;
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
