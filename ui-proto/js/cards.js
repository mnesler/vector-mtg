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
        console.log('Search result:', result);

        // New API returns {cards: [...], count: N, search_term: "..."}
        if (result.cards && Array.isArray(result.cards)) {
            currentResults = result.cards;
            console.log(`Found ${currentResults.length} cards`);
        } else {
            currentResults = [];
            console.log('No cards in result, result structure:', Object.keys(result));
        }

        renderResults(`Search: "${query}"`, currentResults.length);
    } catch (error) {
        console.error('Search failed:', error);
        showError('No cards found or API error');
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
    console.log(`renderResults called: title="${title}", count=${count}, currentResults.length=${currentResults.length}`);

    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('loadingState').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');

    document.getElementById('resultsTitle').textContent = title;
    document.getElementById('resultsCount').textContent = `${count} result${count !== 1 ? 's' : ''}`;

    const grid = document.getElementById('cardGrid');

    if (currentResults.length === 0) {
        console.log('No results to display');
        grid.innerHTML = '<div class="col-span-3 text-center py-8 text-gray-400">No cards found</div>';
        return;
    }

    console.log(`Rendering ${currentResults.length} cards`);
    console.log('Grid element:', grid);
    const html = currentResults.map(card => renderCardCard(card)).join('');
    console.log(`Generated HTML length: ${html.length}`);
    console.log('First 200 chars of HTML:', html.substring(0, 200));
    grid.innerHTML = html;
    console.log('HTML inserted, grid children count:', grid.children.length);
}

function renderCardCard(card) {
    try {
        const rules = card.rules || [];
        const hasRules = rules.length > 0;
        const hasImage = card.image_normal || card.image_small;

        // Escape HTML to prevent injection and rendering issues
        const escapeName = (card.name || 'Unknown').replace(/[<>&"']/g, c => ({
            '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
        })[c]);

        const escapeText = (text) => (text || '').replace(/[<>&"']/g, c => ({
            '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;'
        })[c]);

        return `
            <div class="bg-gray-800 rounded border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer overflow-hidden">
                ${hasImage ? `
                    <div class="relative aspect-[5/7] bg-gray-900">
                        <img
                            src="${card.image_small || card.image_normal}"
                            alt="${escapeName}"
                            class="w-full h-full object-cover"
                            loading="lazy"
                            onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
                        />
                        <div class="hidden absolute inset-0 items-center justify-center bg-gray-900 text-gray-500">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                        </div>
                    </div>
                    <div class="p-1.5 bg-gray-800">
                        <h3 class="text-xs font-semibold text-white truncate" title="${escapeName}">${escapeName}</h3>
                        ${card.mana_cost ? `<p class="text-xs text-blue-300 font-mono truncate">${escapeText(card.mana_cost)}</p>` : ''}
                        <p class="text-xs text-gray-400 truncate">${escapeText(card.type_line || '')}</p>
                        ${hasRules ? `
                            <div class="flex flex-wrap gap-0.5 mt-1">
                                ${rules.slice(0, 3).map(rule => `
                                    <span class="text-xs px-1 py-0.5 bg-purple-900/50 text-purple-300 rounded" title="${escapeText(rule.rule_name)}">
                                        ${escapeText(rule.rule_name.split('_')[0])}
                                    </span>
                                `).join('')}
                                ${rules.length > 3 ? `<span class="text-xs text-gray-500">+${rules.length - 3}</span>` : ''}
                            </div>
                        ` : ''}
                    </div>
                ` : `
                    <div class="p-2 bg-gray-900">
                        <h3 class="text-xs font-bold text-white mb-1">${escapeName}</h3>
                        <p class="text-xs text-gray-400 mb-1">${escapeText(card.type_line)}</p>
                        ${card.oracle_text ? `
                            <p class="text-xs text-gray-300 line-clamp-3">
                                ${escapeText(card.oracle_text)}
                            </p>
                        ` : ''}
                    </div>
                `}
            </div>
        `;
    } catch (error) {
        console.error('Error rendering card:', card, error);
        return `<div class="bg-red-900 rounded p-2 border border-red-700 text-xs">Error: ${card?.name || 'Unknown'}</div>`;
    }
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
