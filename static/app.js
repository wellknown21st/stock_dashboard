/**
 * Stock Data Intelligence Dashboard — Frontend Application
 * 
 * Handles all API interactions, chart rendering, and UI state management.
 * Built with vanilla JS and Chart.js for maximum performance.
 */

// ═══════════════════════════════════════════════════════════════
// State Management
// ═══════════════════════════════════════════════════════════════

const state = {
    companies: [],
    selectedSymbol: null,
    selectedDays: 30,
    currentView: 'overview',
    charts: {
        price: null,
        volume: null,
        prediction: null,
        compare: null,
    },
};

const API_BASE = '';

// ═══════════════════════════════════════════════════════════════
// API Helpers
// ═══════════════════════════════════════════════════════════════

async function apiGet(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `API error: ${res.status}`);
        }
        return await res.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// ═══════════════════════════════════════════════════════════════
// Initialization
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', async () => {
    try {
        await loadCompanies();
        await loadOverviewData();
        hideLoading();
    } catch (error) {
        console.error('Initialization error:', error);
        hideLoading();
        document.getElementById('companyList').innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Connection Error</h3>
                <p>Could not load data. Please run the data collector first.</p>
            </div>`;
    }
});

function hideLoading() {
    const screen = document.getElementById('loading-screen');
    screen.classList.add('hidden');
    setTimeout(() => screen.remove(), 500);
}

// ═══════════════════════════════════════════════════════════════
// Company Management
// ═══════════════════════════════════════════════════════════════

async function loadCompanies() {
    const data = await apiGet('/api/companies');
    state.companies = data.companies;
    renderCompanyList(state.companies);
    populateCompareDropdowns(state.companies);
    document.getElementById('dataStatusText').textContent = `${data.count} companies loaded`;
}

function renderCompanyList(companies) {
    const list = document.getElementById('companyList');
    
    if (!companies.length) {
        list.innerHTML = `
            <div class="empty-state" style="padding: 30px 10px;">
                <div class="empty-icon">📭</div>
                <h3>No Companies Found</h3>
                <p>Run the data collector to populate data</p>
            </div>`;
        return;
    }
    
    list.innerHTML = companies.map(c => `
        <div class="company-item ${state.selectedSymbol === c.symbol ? 'active' : ''}" 
             onclick="selectCompany('${c.symbol}')" 
             id="company-${c.symbol}"
             title="${c.name} (${c.sector})">
            <div class="company-info">
                <div class="company-symbol">${c.symbol}</div>
                <div class="company-name">${c.name}</div>
            </div>
            <div class="company-price">
                <div class="price-value ${c.daily_return >= 0 ? 'price-up' : 'price-down'}">
                    ₹${c.latest_close ? c.latest_close.toLocaleString('en-IN', { maximumFractionDigits: 2 }) : '—'}
                </div>
                <div class="price-change ${c.daily_return >= 0 ? 'price-up' : 'price-down'}">
                    ${c.daily_return >= 0 ? '▲' : '▼'} ${Math.abs(c.daily_return)}%
                </div>
            </div>
        </div>
    `).join('');
}

function filterCompanies(query) {
    const q = query.toLowerCase();
    const filtered = state.companies.filter(c =>
        c.symbol.toLowerCase().includes(q) ||
        c.name.toLowerCase().includes(q) ||
        c.sector.toLowerCase().includes(q)
    );
    renderCompanyList(filtered);
}

async function selectCompany(symbol) {
    state.selectedSymbol = symbol;
    
    // Update active state in sidebar
    document.querySelectorAll('.company-item').forEach(el => el.classList.remove('active'));
    const el = document.getElementById(`company-${symbol}`);
    if (el) el.classList.add('active');
    
    const company = state.companies.find(c => c.symbol === symbol);
    if (company) {
        document.getElementById('pageTitle').textContent = company.name;
        document.getElementById('pageSubtitle').textContent = `${company.symbol} · ${company.sector}`;
    }
    
    // Load data for current view
    if (state.currentView === 'overview') {
        switchView('chart');
    }
    
    await loadViewData(state.currentView);
    
    // Close sidebar on mobile
    if (window.innerWidth <= 1024) {
        toggleSidebar();
    }
}

// ═══════════════════════════════════════════════════════════════
// View Switching
// ═══════════════════════════════════════════════════════════════

function switchView(view) {
    state.currentView = view;
    
    // Update tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.view === view);
    });
    
    // Show/hide sections
    document.querySelectorAll('.view-section').forEach(section => {
        section.classList.toggle('active', section.id === `view-${view}`);
    });
    
    loadViewData(view);
}

async function loadViewData(view) {
    switch (view) {
        case 'overview':
            await loadOverviewData();
            break;
        case 'chart':
            if (state.selectedSymbol) await loadChartData();
            break;
        case 'summary':
            if (state.selectedSymbol) await loadSummaryData();
            break;
        case 'predict':
            if (state.selectedSymbol) await loadPredictionData();
            break;
        case 'insights':
            await loadInsightsData();
            break;
    }
}

// ═══════════════════════════════════════════════════════════════
// Overview
// ═══════════════════════════════════════════════════════════════

async function loadOverviewData() {
    try {
        const [gainers, losers, volatile, sectors] = await Promise.all([
            apiGet('/api/gainers?limit=5'),
            apiGet('/api/losers?limit=5'),
            apiGet('/api/volatility?limit=1'),
            apiGet('/api/sectors'),
        ]);
        
        // Stats
        document.getElementById('statCompanies').textContent = state.companies.length;
        
        if (gainers.top_gainers.length) {
            const g = gainers.top_gainers[0];
            document.getElementById('statGainer').textContent = g.symbol;
            document.getElementById('statGainerChange').textContent = `+${g.daily_return_pct}%`;
        }
        
        if (losers.top_losers.length) {
            const l = losers.top_losers[0];
            document.getElementById('statLoser').textContent = l.symbol;
            document.getElementById('statLoserChange').textContent = `${l.daily_return_pct}%`;
        }
        
        if (volatile.most_volatile.length) {
            const v = volatile.most_volatile[0];
            document.getElementById('statVolatile').textContent = v.symbol;
            document.getElementById('statVolatileScore').textContent = `Score: ${v.volatility_score}`;
        }
        
        // Sectors
        renderSectors(sectors.sectors);
        
        // Gainers & Losers lists
        renderInsightList('gainersList', gainers.top_gainers, true);
        renderInsightList('losersList', losers.top_losers, false);
        
    } catch (error) {
        console.error('Overview error:', error);
    }
}

function renderSectors(sectors) {
    const grid = document.getElementById('sectorGrid');
    grid.innerHTML = sectors.map(s => `
        <div class="sector-card">
            <div class="sector-name">${s.sector}</div>
            <div class="sector-return ${s.avg_daily_return_pct >= 0 ? 'price-up' : 'price-down'}">
                ${s.avg_daily_return_pct >= 0 ? '+' : ''}${s.avg_daily_return_pct}%
            </div>
            <div class="sector-companies">${s.num_companies} ${s.num_companies === 1 ? 'company' : 'companies'}</div>
        </div>
    `).join('');
}

function renderInsightList(containerId, items, isPositive) {
    const list = document.getElementById(containerId);
    list.innerHTML = items.map((item, i) => `
        <li class="insight-item" onclick="selectCompany('${item.symbol}')">
            <span class="rank">${i + 1}</span>
            <div class="stock-info">
                <div class="stock-symbol">${item.symbol}</div>
                <div class="stock-name">${item.company_name}</div>
            </div>
            <span class="change-badge ${isPositive ? 'positive' : 'negative'}">
                ${item.daily_return_pct >= 0 ? '+' : ''}${item.daily_return_pct}%
            </span>
        </li>
    `).join('');
}

// ═══════════════════════════════════════════════════════════════
// Chart View
// ═══════════════════════════════════════════════════════════════

async function loadChartData() {
    if (!state.selectedSymbol) return;
    
    try {
        const data = await apiGet(`/api/data/${state.selectedSymbol}?days=${state.selectedDays}`);
        document.getElementById('chartTitle').textContent = 
            `${data.company_name} (${data.symbol}) — ${state.selectedDays} Day Chart`;
        
        renderPriceChart(data.data);
        renderVolumeChart(data.data);
    } catch (error) {
        console.error('Chart error:', error);
    }
}

function renderPriceChart(data) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (state.charts.price) state.charts.price.destroy();
    
    const labels = data.map(d => d.date);
    const closes = data.map(d => d.close);
    const ma7 = data.map(d => d.ma_7);
    const ma20 = data.map(d => d.ma_20);
    
    // Gradient for main line
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.25)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
    
    state.charts.price = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Close Price',
                    data: closes,
                    borderColor: '#6366f1',
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: data.length > 60 ? 0 : 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#6366f1',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                },
                {
                    label: '7-Day MA',
                    data: ma7,
                    borderColor: '#06b6d4',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                },
                {
                    label: '20-Day MA',
                    data: ma20,
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    borderDash: [3, 3],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 20,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ₹${context.parsed.y.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        maxTicksLimit: 10,
                        maxRotation: 0,
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.04)',
                    },
                },
                y: {
                    ticks: {
                        color: '#64748b',
                        font: { family: 'Inter', size: 11 },
                        callback: (v) => '₹' + v.toLocaleString('en-IN'),
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.04)',
                    },
                },
            },
        },
    });
}

function renderVolumeChart(data) {
    const ctx = document.getElementById('volumeChart').getContext('2d');
    
    if (state.charts.volume) state.charts.volume.destroy();
    
    const labels = data.map(d => d.date);
    const volumes = data.map(d => d.volume);
    const colors = data.map(d => d.daily_return >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)');
    
    state.charts.volume = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Volume',
                data: volumes,
                backgroundColor: colors,
                borderRadius: 3,
                borderSkipped: false,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => `Volume: ${ctx.parsed.y.toLocaleString('en-IN')}`,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 10, maxRotation: 0 },
                    grid: { display: false },
                },
                y: {
                    ticks: {
                        color: '#64748b',
                        font: { size: 10 },
                        callback: (v) => {
                            if (v >= 1e7) return (v / 1e7).toFixed(1) + 'Cr';
                            if (v >= 1e5) return (v / 1e5).toFixed(1) + 'L';
                            if (v >= 1e3) return (v / 1e3).toFixed(1) + 'K';
                            return v;
                        },
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
            },
        },
    });
}

function changeTimeRange(days) {
    state.selectedDays = days;
    document.querySelectorAll('.time-btn').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.days) === days);
    });
    loadChartData();
}

// ═══════════════════════════════════════════════════════════════
// Summary View
// ═══════════════════════════════════════════════════════════════

async function loadSummaryData() {
    if (!state.selectedSymbol) return;
    
    const container = document.getElementById('summaryContent');
    
    try {
        const data = await apiGet(`/api/summary/${state.selectedSymbol}`);
        
        container.innerHTML = `
            <div class="stats-grid" style="margin-bottom: 24px;">
                <div class="stat-card accent-indigo">
                    <div class="stat-label">Current Close</div>
                    <div class="stat-value">₹${data.price_summary.current_close?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '—'}</div>
                </div>
                <div class="stat-card accent-green">
                    <div class="stat-label">52-Week High</div>
                    <div class="stat-value price-up">₹${data.price_summary.high_52w?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '—'}</div>
                </div>
                <div class="stat-card accent-red">
                    <div class="stat-label">52-Week Low</div>
                    <div class="stat-value price-down">₹${data.price_summary.low_52w?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '—'}</div>
                </div>
                <div class="stat-card accent-amber">
                    <div class="stat-label">Trend</div>
                    <div class="stat-value" style="font-size: 1.3rem;">${data.trend}</div>
                </div>
            </div>
            
            <div class="summary-grid">
                <div class="summary-section">
                    <h4>💰 Price Summary</h4>
                    <div class="summary-row">
                        <span class="label">Average Close</span>
                        <span class="value">₹${data.price_summary.avg_close?.toLocaleString('en-IN') || '—'}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Median Close</span>
                        <span class="value">₹${data.price_summary.median_close?.toLocaleString('en-IN') || '—'}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Period Return</span>
                        <span class="value ${data.returns.period_return_pct >= 0 ? 'price-up' : 'price-down'}">
                            ${data.returns.period_return_pct >= 0 ? '+' : ''}${data.returns.period_return_pct}%
                        </span>
                    </div>
                </div>
                
                <div class="summary-section">
                    <h4>📊 Volume Analysis</h4>
                    <div class="summary-row">
                        <span class="label">Total Volume</span>
                        <span class="value">${formatLargeNumber(data.volume_summary.total_volume)}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Avg Daily Volume</span>
                        <span class="value">${formatLargeNumber(data.volume_summary.avg_daily_volume)}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Max Volume Day</span>
                        <span class="value">${formatLargeNumber(data.volume_summary.max_volume_day)}</span>
                    </div>
                </div>
                
                <div class="summary-section">
                    <h4>📈 Returns</h4>
                    <div class="summary-row">
                        <span class="label">Avg Daily Return</span>
                        <span class="value">${data.returns.avg_daily_return_pct}%</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Best Day</span>
                        <span class="value price-up">+${data.returns.best_day_pct}%</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Worst Day</span>
                        <span class="value price-down">${data.returns.worst_day_pct}%</span>
                    </div>
                </div>
                
                <div class="summary-section">
                    <h4>⚡ Risk Metrics</h4>
                    <div class="summary-row">
                        <span class="label">Volatility Score</span>
                        <span class="value">${data.risk.volatility_score}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Std Deviation</span>
                        <span class="value">₹${data.risk.std_deviation}</span>
                    </div>
                    <div class="summary-row">
                        <span class="label">Trading Days</span>
                        <span class="value">${data.period.trading_days}</span>
                    </div>
                </div>
            </div>
        `;
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Error Loading Summary</h3>
                <p>${error.message}</p>
            </div>`;
    }
}

// ═══════════════════════════════════════════════════════════════
// Compare View
// ═══════════════════════════════════════════════════════════════

function populateCompareDropdowns(companies) {
    const s1 = document.getElementById('compareStock1');
    const s2 = document.getElementById('compareStock2');
    
    const options = companies.map(c => `<option value="${c.symbol}">${c.symbol} — ${c.name}</option>`).join('');
    
    s1.innerHTML = '<option value="">Select Stock 1</option>' + options;
    s2.innerHTML = '<option value="">Select Stock 2</option>' + options;
}

async function compareStocks() {
    const s1 = document.getElementById('compareStock1').value;
    const s2 = document.getElementById('compareStock2').value;
    const days = document.getElementById('comparePeriod').value;
    const container = document.getElementById('compareResults');
    
    if (!s1 || !s2) {
        alert('Please select both stocks to compare');
        return;
    }
    
    if (s1 === s2) {
        alert('Please select two different stocks');
        return;
    }
    
    container.innerHTML = '<div class="empty-state"><div class="loading-spinner"></div><p>Comparing...</p></div>';
    
    try {
        const data = await apiGet(`/api/compare?symbol1=${s1}&symbol2=${s2}&days=${days}`);
        
        const winner = data.winner;
        
        container.innerHTML = `
            <div class="compare-results">
                <div class="card" style="${data.stock1.symbol === winner ? 'border-color: rgba(16, 185, 129, 0.4);' : ''}">
                    <h3 style="margin-bottom: 16px; font-size: 1.1rem;">
                        ${data.stock1.symbol === winner ? '🏆 ' : ''}${data.stock1.company_name}
                        <span style="color: var(--text-muted); font-weight: 400; font-size: 0.85rem;"> (${data.stock1.symbol})</span>
                    </h3>
                    <div class="compare-metric">
                        <span class="metric-label">Current Close</span>
                        <span class="metric-value">₹${data.stock1.current_close?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Period Return</span>
                        <span class="metric-value ${data.stock1.period_return_pct >= 0 ? 'price-up' : 'price-down'}">
                            ${data.stock1.period_return_pct >= 0 ? '+' : ''}${data.stock1.period_return_pct}%
                        </span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Avg Daily Return</span>
                        <span class="metric-value">${data.stock1.avg_daily_return_pct}%</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Volatility</span>
                        <span class="metric-value">${data.stock1.volatility}%</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">High</span>
                        <span class="metric-value">₹${data.stock1.high?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Low</span>
                        <span class="metric-value">₹${data.stock1.low?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                </div>
                
                <div class="card" style="${data.stock2.symbol === winner ? 'border-color: rgba(16, 185, 129, 0.4);' : ''}">
                    <h3 style="margin-bottom: 16px; font-size: 1.1rem;">
                        ${data.stock2.symbol === winner ? '🏆 ' : ''}${data.stock2.company_name}
                        <span style="color: var(--text-muted); font-weight: 400; font-size: 0.85rem;"> (${data.stock2.symbol})</span>
                    </h3>
                    <div class="compare-metric">
                        <span class="metric-label">Current Close</span>
                        <span class="metric-value">₹${data.stock2.current_close?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Period Return</span>
                        <span class="metric-value ${data.stock2.period_return_pct >= 0 ? 'price-up' : 'price-down'}">
                            ${data.stock2.period_return_pct >= 0 ? '+' : ''}${data.stock2.period_return_pct}%
                        </span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Avg Daily Return</span>
                        <span class="metric-value">${data.stock2.avg_daily_return_pct}%</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Volatility</span>
                        <span class="metric-value">${data.stock2.volatility}%</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">High</span>
                        <span class="metric-value">₹${data.stock2.high?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div class="compare-metric">
                        <span class="metric-label">Low</span>
                        <span class="metric-value">₹${data.stock2.low?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </div>
                </div>
            </div>
            
            <div class="correlation-badge">
                <span>Correlation:</span>
                <span class="correlation-value">${data.correlation ?? 'N/A'}</span>
                <span style="color: var(--text-muted);">(${data.correlation_interpretation})</span>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-header">
                    <div class="card-title"><span class="icon">📉</span> Normalized Performance Comparison</div>
                </div>
                <div class="chart-container">
                    <canvas id="compareChart"></canvas>
                </div>
            </div>
        `;
        
        // Render comparison chart
        renderCompareChart(data.normalized_series);
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Comparison Error</h3>
                <p>${error.message}</p>
            </div>`;
    }
}

function renderCompareChart(series) {
    const ctx = document.getElementById('compareChart').getContext('2d');
    
    if (state.charts.compare) state.charts.compare.destroy();
    
    const maxLen = Math.max(series.stock1.dates.length, series.stock2.dates.length);
    const allDates = series.stock1.dates.length >= series.stock2.dates.length 
        ? series.stock1.dates : series.stock2.dates;
    
    state.charts.compare = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: series.stock1.symbol,
                    data: series.stock1.values,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
                {
                    label: series.stock2.symbol,
                    data: series.stock2.values,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 2.5,
                    fill: false,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        padding: 20,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y}%`,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 10, maxRotation: 0 },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
                y: {
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        callback: (v) => v + '%',
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════
// Prediction View
// ═══════════════════════════════════════════════════════════════

async function loadPredictionData() {
    if (!state.selectedSymbol) return;
    
    const container = document.getElementById('predictContent');
    const metrics = document.getElementById('predictMetrics');
    
    container.innerHTML = '<div class="empty-state"><div class="loading-spinner"></div><p>Running ML model...</p></div>';
    
    try {
        const [prediction, historical] = await Promise.all([
            apiGet(`/api/predict/${state.selectedSymbol}?days=7`),
            apiGet(`/api/data/${state.selectedSymbol}?days=60`),
        ]);
        
        if (prediction.error) {
            container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>${prediction.error}</h3></div>`;
            return;
        }
        
        document.getElementById('predictTitle').textContent = 
            `${prediction.company_name} — 7-Day Price Prediction`;
        
        // Model metrics
        metrics.style.display = 'flex';
        metrics.innerHTML = `
            <div class="metric-pill">
                <span class="metric-key">Model:</span>
                <span class="metric-val">${prediction.model}</span>
            </div>
            <div class="metric-pill">
                <span class="metric-key">Train R²:</span>
                <span class="metric-val">${prediction.train_r2_score}</span>
            </div>
            <div class="metric-pill">
                <span class="metric-key">Test R²:</span>
                <span class="metric-val">${prediction.test_r2_score}</span>
            </div>
        `;
        
        container.innerHTML = '';
        
        renderPredictionChart(historical.data, prediction.predictions);
        
    } catch (error) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <h3>Prediction Error</h3>
                <p>${error.message}</p>
            </div>`;
        metrics.style.display = 'none';
    }
}

function renderPredictionChart(historical, predictions) {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    
    if (state.charts.prediction) state.charts.prediction.destroy();
    
    // Last 30 days of historical + predictions
    const recentHistorical = historical.slice(-30);
    
    const histLabels = recentHistorical.map(d => d.date);
    const histCloses = recentHistorical.map(d => d.close);
    
    const predLabels = predictions.map(p => p.date);
    const predValues = predictions.map(p => p.predicted_close);
    
    // Combine labels
    const allLabels = [...histLabels, ...predLabels];
    
    // Historical data (null padded for predictions)
    const histData = [...histCloses, ...new Array(predLabels.length).fill(null)];
    
    // Prediction data (null padded for historical, starts from last historical point)
    const predData = [...new Array(histLabels.length - 1).fill(null), histCloses[histCloses.length - 1], ...predValues];
    
    const gradientHist = ctx.createLinearGradient(0, 0, 0, 400);
    gradientHist.addColorStop(0, 'rgba(99, 102, 241, 0.2)');
    gradientHist.addColorStop(1, 'rgba(99, 102, 241, 0.0)');
    
    state.charts.prediction = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: 'Historical Close',
                    data: histData,
                    borderColor: '#6366f1',
                    backgroundColor: gradientHist,
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
                {
                    label: 'Predicted Close',
                    data: predData,
                    borderColor: '#a855f7',
                    borderWidth: 2.5,
                    borderDash: [8, 4],
                    fill: false,
                    tension: 0.3,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    pointBackgroundColor: '#a855f7',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: {
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        usePointStyle: true,
                        padding: 20,
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(17, 24, 39, 0.95)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#94a3b8',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ₹${ctx.parsed.y?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || 'N/A'}`,
                    },
                },
            },
            scales: {
                x: {
                    ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 12, maxRotation: 45 },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
                y: {
                    ticks: {
                        color: '#64748b',
                        font: { size: 11 },
                        callback: (v) => '₹' + v.toLocaleString('en-IN'),
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.04)' },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════
// Insights View
// ═══════════════════════════════════════════════════════════════

async function loadInsightsData() {
    try {
        const [volatile, correlation] = await Promise.all([
            apiGet('/api/volatility?limit=10'),
            apiGet('/api/correlation'),
        ]);
        
        // Volatility list
        const volList = document.getElementById('volatilityList');
        volList.innerHTML = volatile.most_volatile.map((v, i) => `
            <li class="insight-item" onclick="selectCompany('${v.symbol}')">
                <span class="rank">${i + 1}</span>
                <div class="stock-info">
                    <div class="stock-symbol">${v.symbol}</div>
                    <div class="stock-name">${v.company_name}</div>
                </div>
                <span class="change-badge ${v.daily_return_pct >= 0 ? 'positive' : 'negative'}">
                    Score: ${v.volatility_score}
                </span>
            </li>
        `).join('');
        
        // Correlation matrix
        renderCorrelationMatrix(correlation);
        
    } catch (error) {
        console.error('Insights error:', error);
    }
}

function renderCorrelationMatrix(data) {
    const container = document.getElementById('correlationMatrix');
    
    if (!data.symbols || data.error) {
        container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><h3>${data.error || 'No data'}</h3></div>`;
        return;
    }
    
    const symbols = data.symbols;
    const matrix = data.matrix;
    
    let html = '<table class="corr-table"><thead><tr><th></th>';
    symbols.forEach(s => html += `<th>${s}</th>`);
    html += '</tr></thead><tbody>';
    
    symbols.forEach(row => {
        html += `<tr><th>${row}</th>`;
        symbols.forEach(col => {
            const val = matrix[row]?.[col] ?? 0;
            const color = getCorrelationColor(val);
            html += `<td style="background-color: ${color}; color: ${Math.abs(val) > 0.5 ? '#fff' : 'var(--text-primary)'}">${val.toFixed(2)}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function getCorrelationColor(val) {
    if (val >= 0.8) return 'rgba(16, 185, 129, 0.6)';
    if (val >= 0.5) return 'rgba(16, 185, 129, 0.35)';
    if (val >= 0.2) return 'rgba(16, 185, 129, 0.15)';
    if (val > -0.2) return 'rgba(255, 255, 255, 0.03)';
    if (val > -0.5) return 'rgba(239, 68, 68, 0.15)';
    if (val > -0.8) return 'rgba(239, 68, 68, 0.35)';
    return 'rgba(239, 68, 68, 0.6)';
}

// ═══════════════════════════════════════════════════════════════
// Utility Functions
// ═══════════════════════════════════════════════════════════════

function formatLargeNumber(num) {
    if (!num) return '0';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e7) return (num / 1e7).toFixed(2) + 'Cr';
    if (num >= 1e5) return (num / 1e5).toFixed(2) + 'L';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toLocaleString('en-IN');
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

async function refreshData() {
    const btn = document.querySelector('.btn-refresh');
    btn.textContent = '↻ Refreshing...';
    btn.disabled = true;
    
    try {
        await loadCompanies();
        await loadViewData(state.currentView);
    } catch (e) {
        console.error('Refresh error:', e);
    } finally {
        btn.textContent = '↻ Refresh';
        btn.disabled = false;
    }
}
