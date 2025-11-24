/**
 * Rules page logic
 */

let allRules = [];
let allCategories = [];
let currentFilter = null;
let currentRuleDetails = null;

async function init() {
    await loadCategories();
    await loadRules();
}

async function loadCategories() {
    try {
        const response = await api.getCategories();
        allCategories = response.categories.sort((a, b) => b.card_count - a.card_count);

        renderCategoryFilters();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

async function loadRules() {
    document.getElementById('loadingState').classList.remove('hidden');

    try {
        const response = await api.listRules(currentFilter);
        allRules = response.rules;

        document.getElementById('loadingState').classList.add('hidden');
        renderRules(allRules);
    } catch (error) {
        console.error('Failed to load rules:', error);
        document.getElementById('loadingState').classList.add('hidden');
    }
}

function renderCategoryFilters() {
    const container = document.getElementById('categoryFilters');

    // Add category buttons
    allCategories.forEach(category => {
        const button = document.createElement('button');
        button.className = 'category-btn px-4 py-2 rounded bg-gray-700 hover:bg-gray-600';
        button.textContent = `${category.name} (${formatNumber(category.card_count)})`;
        button.onclick = () => filterByCategory(category.name);
        container.appendChild(button);
    });
}

function filterByCategory(category) {
    currentFilter = category;

    // Update button states
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active', 'bg-blue-600');
        btn.classList.add('bg-gray-700');
    });

    event.target.classList.add('active', 'bg-blue-600');
    event.target.classList.remove('bg-gray-700');

    loadRules();
}

function renderRules(rules) {
    const grid = document.getElementById('rulesGrid');

    if (rules.length === 0) {
        grid.innerHTML = '<div class="col-span-3 text-center py-12 text-gray-400">No rules found</div>';
        return;
    }

    grid.innerHTML = rules.map(rule => `
        <div class="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-blue-500 transition-colors cursor-pointer"
             onclick="showRuleDetails('${rule.rule_name}')">
            <div class="flex justify-between items-start mb-3">
                <h3 class="text-lg font-semibold text-white flex-1">
                    ${rule.rule_name.replace(/_/g, ' ')}
                </h3>
                <span class="text-sm font-mono text-gray-400">${formatNumber(rule.card_count)}</span>
            </div>

            ${rule.category ? `
                <span class="inline-block px-2 py-1 rounded text-xs font-semibold mb-3"
                      style="background-color: ${getCategoryColor(rule.category)}33; color: ${getCategoryColor(rule.category)}">
                    ${rule.category}
                </span>
            ` : ''}

            <p class="text-sm text-gray-300 mb-2">${rule.rule_template}</p>

            ${rule.rule_pattern ? `
                <p class="text-xs text-gray-500 font-mono truncate">
                    Pattern: ${rule.rule_pattern}
                </p>
            ` : ''}
        </div>
    `).join('');
}

async function showRuleDetails(ruleName) {
    // Show modal
    document.getElementById('ruleModal').classList.remove('hidden');

    // Find rule
    const rule = allRules.find(r => r.rule_name === ruleName);
    if (!rule) return;

    currentRuleDetails = rule;

    // Set modal content
    document.getElementById('modalRuleName').textContent = rule.rule_name.replace(/_/g, ' ');
    document.getElementById('modalCategory').textContent = rule.category || 'Uncategorized';
    document.getElementById('modalTemplate').textContent = rule.rule_template;
    document.getElementById('modalCardCount').textContent = formatNumber(rule.card_count);

    // Show loading state for cards
    const cardsContainer = document.getElementById('modalCards');
    cardsContainer.innerHTML = `
        <div class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p class="mt-2 text-sm text-gray-400">Loading cards...</p>
        </div>
    `;

    // Load cards for this rule
    try {
        const response = await api.getRuleCards(ruleName, 20);
        const cards = response.cards || [];

        cardsContainer.innerHTML = cards.map(card => `
            <div class="bg-gray-900 rounded p-3 hover:bg-gray-800 transition-colors">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <p class="font-semibold text-white">${card.name}</p>
                        <p class="text-sm text-gray-400 mt-1">${card.type_line}</p>
                        ${card.oracle_text ? `
                            <p class="text-xs text-gray-500 mt-2 line-clamp-2">${card.oracle_text}</p>
                        ` : ''}
                    </div>
                    ${card.mana_cost ? `
                        <span class="text-sm font-mono text-blue-300 ml-2">${card.mana_cost}</span>
                    ` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load rule cards:', error);
        document.getElementById('modalCards').innerHTML = '<p class="text-gray-400">Failed to load cards</p>';
    }
}

function closeModal() {
    document.getElementById('ruleModal').classList.add('hidden');
}

function filterRules() {
    const searchTerm = document.getElementById('ruleSearch').value.toLowerCase();

    if (!searchTerm) {
        renderRules(allRules);
        return;
    }

    const filtered = allRules.filter(rule =>
        rule.rule_name.toLowerCase().includes(searchTerm) ||
        (rule.rule_template && rule.rule_template.toLowerCase().includes(searchTerm)) ||
        (rule.category && rule.category.toLowerCase().includes(searchTerm))
    );

    renderRules(filtered);
}

// Close modal on escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Close modal on background click
document.getElementById('ruleModal').addEventListener('click', (e) => {
    if (e.target.id === 'ruleModal') {
        closeModal();
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
