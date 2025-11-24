/**
 * Dashboard page logic
 */

let topRulesChart = null;
let categoryChart = null;

async function loadDashboard() {
    try {
        // Load statistics
        const stats = await api.getStats();
        renderStatsCards(stats);

        // Load top rules chart
        await loadTopRulesChart(stats.top_rules);

        // Load category chart
        await loadCategoryChart();

        // Load table
        await loadTopRulesTable(stats.top_rules, stats.total_cards);

        // Hide main loading overlay
        hideMainLoading();

    } catch (error) {
        console.error('Failed to load dashboard:', error);
        hideMainLoading();
        showError('Failed to load dashboard data. Make sure the API server is running.');
    }
}

function hideMainLoading() {
    const loadingOverlay = document.getElementById('dashboardLoading');
    if (loadingOverlay) {
        loadingOverlay.style.opacity = '0';
        setTimeout(() => {
            loadingOverlay.style.display = 'none';
        }, 300);
    }
}

function renderStatsCards(stats) {
    const statsGrid = document.getElementById('statsGrid');
    statsGrid.innerHTML = `
        <div class="bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg p-6 border border-blue-500/20">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-blue-100 text-sm font-medium">Total Cards</p>
                    <p class="text-3xl font-bold text-white mt-1">${formatNumber(stats.total_cards)}</p>
                </div>
                <div class="bg-blue-500/30 rounded-lg p-3">
                    <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                </div>
            </div>
        </div>

        <div class="bg-gradient-to-br from-purple-600 to-purple-700 rounded-lg p-6 border border-purple-500/20">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-purple-100 text-sm font-medium">Total Rules</p>
                    <p class="text-3xl font-bold text-white mt-1">${formatNumber(stats.total_rules)}</p>
                </div>
                <div class="bg-purple-500/30 rounded-lg p-3">
                    <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                </div>
            </div>
        </div>

        <div class="bg-gradient-to-br from-green-600 to-green-700 rounded-lg p-6 border border-green-500/20">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-green-100 text-sm font-medium">Cards with Rules</p>
                    <p class="text-3xl font-bold text-white mt-1">${formatNumber(stats.cards_with_rules)}</p>
                    <p class="text-green-200 text-xs mt-1">${stats.coverage_percentage}% coverage</p>
                </div>
                <div class="bg-green-500/30 rounded-lg p-3">
                    <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
            </div>
        </div>

        <div class="bg-gradient-to-br from-orange-600 to-orange-700 rounded-lg p-6 border border-orange-500/20">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-orange-100 text-sm font-medium">Avg Rules/Card</p>
                    <p class="text-3xl font-bold text-white mt-1">${stats.avg_rules_per_card.toFixed(2)}</p>
                </div>
                <div class="bg-orange-500/30 rounded-lg p-3">
                    <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                    </svg>
                </div>
            </div>
        </div>
    `;
}

async function loadTopRulesChart(topRules) {
    // Hide loading, show chart
    document.getElementById('topRulesChartLoading').classList.add('hidden');
    document.getElementById('topRulesChart').classList.remove('hidden');

    const ctx = document.getElementById('topRulesChart').getContext('2d');

    if (topRulesChart) {
        topRulesChart.destroy();
    }

    const labels = topRules.map(r => r.rule_name.replace(/_/g, ' '));
    const data = topRules.map(r => r.card_count);
    const colors = topRules.map(r => getCategoryColor(r.category));

    topRulesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Card Count',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c + 'cc'),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${formatNumber(context.raw)} cards`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return formatNumber(value);
                        }
                    },
                    grid: {
                        color: '#374151'
                    }
                },
                x: {
                    ticks: {
                        color: '#9ca3af',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

async function loadCategoryChart() {
    try {
        const categories = await api.getCategories();

        // Hide loading, show chart
        document.getElementById('categoryChartLoading').classList.add('hidden');
        document.getElementById('categoryChart').classList.remove('hidden');

        const ctx = document.getElementById('categoryChart').getContext('2d');

        if (categoryChart) {
            categoryChart.destroy();
        }

        const sortedCategories = categories.categories
            .sort((a, b) => b.card_count - a.card_count)
            .slice(0, 10);

        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sortedCategories.map(c => c.name),
                datasets: [{
                    data: sortedCategories.map(c => c.card_count),
                    backgroundColor: sortedCategories.map(c => getCategoryColor(c.name)),
                    borderColor: '#1f2937',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#9ca3af',
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = formatNumber(context.raw);
                                return `${label}: ${value} cards`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to load category chart:', error);
    }
}

async function loadTopRulesTable(topRules, totalCards) {
    // Hide loading, show table
    document.getElementById('tableLoading').classList.add('hidden');
    document.getElementById('tableContainer').classList.remove('hidden');

    const tbody = document.querySelector('#topRulesTable tbody');

    tbody.innerHTML = topRules.map(rule => {
        const percentage = formatPercentage(rule.card_count, totalCards);
        const categoryColor = getCategoryColor(rule.category);

        return `
            <tr class="hover:bg-gray-700/50">
                <td class="py-3 px-4">
                    <span class="font-medium">${rule.rule_name.replace(/_/g, ' ')}</span>
                </td>
                <td class="py-3 px-4">
                    <span class="inline-block px-2 py-1 rounded text-xs font-semibold" style="background-color: ${categoryColor}33; color: ${categoryColor}">
                        ${rule.category || 'Uncategorized'}
                    </span>
                </td>
                <td class="py-3 px-4 text-right font-mono">${formatNumber(rule.card_count)}</td>
                <td class="py-3 px-4 text-right text-gray-400">${percentage}</td>
            </tr>
        `;
    }).join('');
}

function showError(message) {
    const statsGrid = document.getElementById('statsGrid');
    statsGrid.innerHTML = `
        <div class="col-span-4 bg-red-900/20 border border-red-500/50 rounded-lg p-6 text-center">
            <p class="text-red-400">${message}</p>
        </div>
    `;
}

// Quick search handler
document.getElementById('quickSearch').addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
        const query = e.target.value.trim();
        if (query) {
            window.location.href = `cards.html?search=${encodeURIComponent(query)}`;
        }
    }
});

// Load dashboard on page load
document.addEventListener('DOMContentLoaded', loadDashboard);
