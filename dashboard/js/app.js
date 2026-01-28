/**
 * Market Ritual Dashboard - JavaScript Application
 * Handles theme switching, time detection, data loading, and rendering
 */

// ===================================
// Global State
// ===================================
let currentTheme = 'light';
let currentTab = 'today';
let reportData = null;

// ===================================
// Initialize App
// ===================================
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    initializeTabs();
    initializeScrollTop();
    updateCurrentTime();
    detectTodayRitual();
    
    // Update time every minute
    setInterval(updateCurrentTime, 60000);
});

// ===================================
// Theme Management
// ===================================
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const savedTheme = localStorage.getItem('theme');
    
    // Check for saved theme or system preference
    if (savedTheme) {
        currentTheme = savedTheme;
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        currentTheme = 'dark';
    }
    
    applyTheme(currentTheme);
    
    themeToggle.addEventListener('click', toggleTheme);
}

function applyTheme(theme) {
    currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    const themeIcon = document.querySelector('.theme-icon');
    themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
}

// ===================================
// Time Management
// ===================================
function updateCurrentTime() {
    const now = new Date();
    const options = {
        timeZone: 'America/Chicago',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        weekday: 'short',
        month: 'short',
        day: 'numeric'
    };
    
    const timeString = now.toLocaleString('en-US', options);
    document.getElementById('currentTime').textContent = timeString + ' CST';
}

function getCurrentCSTTime() {
    const now = new Date();
    const options = {
        timeZone: 'America/Chicago',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    };
    
    const timeString = now.toLocaleString('en-US', options);
    const [hours, minutes] = timeString.split(':').map(Number);
    return { hours, minutes };
}

// ===================================
// Auto-Detection Logic
// ===================================
function detectTodayRitual() {
    const { hours, minutes } = getCurrentCSTTime();
    const totalMinutes = hours * 60 + minutes;
    
    // Before 11:00 AM CST (660 minutes)
    if (totalMinutes < 660) {
        loadReport('premarket');
    }
    // After 3:10 PM CST (15:10 = 910 minutes)
    else if (totalMinutes >= 910) {
        loadReport('postmarket');
    }
    // Market in session
    else {
        showInSessionMessage();
    }
}

function showInSessionMessage() {
    hideAllViews();
    const inSessionMessage = document.getElementById('inSessionMessage');
    inSessionMessage.style.display = 'block';
    
    const { hours, minutes } = getCurrentCSTTime();
    const currentTime = `${hours}:${minutes.toString().padStart(2, '0')} CST`;
    document.getElementById('sessionTime').innerHTML = `
        <strong>Current Time:</strong> ${currentTime}<br>
        Market is open from 9:30 AM to 4:00 PM CST
    `;
}

// ===================================
// Tab Management
// ===================================
function initializeTabs() {
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabType = tab.dataset.tab;
            setActiveTab(tabType);
            
            if (tabType === 'today') {
                detectTodayRitual();
            } else {
                loadReport(tabType);
            }
        });
    });
}

function setActiveTab(tabType) {
    currentTab = tabType;
    
    // Update tab UI
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.tab === tabType) {
            tab.classList.add('active');
        }
    });
}

// ===================================
// Data Loading
// ===================================
async function loadReport(type) {
    hideAllViews();
    showLoading();
    
    try {
        const response = await fetch(`./data/${type}.json`);
        
        if (!response.ok) {
            throw new Error(`Failed to load ${type} data`);
        }
        
        reportData = await response.json();
        renderReport(type, reportData);
        
    } catch (error) {
        console.error('Error loading report:', error);
        showError(`Unable to load ${type} report. Please ensure the data file exists.`);
    }
}

// ===================================
// View Management
// ===================================
function hideAllViews() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    document.getElementById('inSessionMessage').style.display = 'none';
    document.getElementById('reportContainer').style.display = 'none';
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function showError(message) {
    hideAllViews();
    const errorDiv = document.getElementById('error');
    errorDiv.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

// ===================================
// Report Rendering
// ===================================
function renderReport(type, data) {
    hideAllViews();
    
    const reportContainer = document.getElementById('reportContainer');
    reportContainer.style.display = 'block';
    
    // Update header
    document.getElementById('reportTitle').textContent = 
        type === 'premarket' ? 'Pre-Market Ritual' : 'Post-Market Ritual';
    document.getElementById('reportDate').textContent = data.date || 'Today';
    document.getElementById('reportBadge').textContent = 
        type === 'premarket' ? 'Morning Brief' : 'Daily Summary';
    
    // Render content
    const reportContent = document.getElementById('reportContent');
    reportContent.innerHTML = '';
    
    // Render futures/market snapshot
    if (data.snapshot) {
        reportContent.appendChild(renderSnapshot(data.snapshot, type));
    }
    
    // Render key levels
    if (data.key_levels) {
        reportContent.appendChild(renderKeyLevels(data.key_levels));
    }
    
    // Render intraday levels
    if (data.intraday_levels) {
        reportContent.appendChild(renderIntradayLevels(data.intraday_levels));
    }
    
    // Render breadth
    if (data.breadth) {
        reportContent.appendChild(renderBreadth(data.breadth));
    }
    
    // Render sentiment
    if (data.sentiment) {
        reportContent.appendChild(renderSentiment(data.sentiment));
    }
    
    // Render market context
    if (data.market_context) {
        reportContent.appendChild(renderMarketContext(data.market_context));
    }
    
    // Render all sections
    if (data.sections) {
        Object.entries(data.sections).forEach(([key, value]) => {
            reportContent.appendChild(renderSection(formatSectionTitle(key), value));
        });
    }
    
    // Render RS leaders
    if (data.rs_leaders) {
        reportContent.appendChild(renderRSLeaders(data.rs_leaders));
    }
    
    // Render checklist
    if (data.checklist) {
        reportContent.appendChild(renderChecklist(data.checklist));
    }
}

// ===================================
// Component Renderers
// ===================================
function renderSnapshot(snapshot, type) {
    const card = createCard('📊', 'Market Snapshot');
    
    const metricsGrid = document.createElement('div');
    metricsGrid.className = 'metrics-grid';
    
    Object.entries(snapshot).forEach(([key, value]) => {
        const metric = document.createElement('div');
        metric.className = 'metric-item';
        
        const isPositive = value.change && parseFloat(value.change) > 0;
        const changeClass = isPositive ? 'positive' : 'negative';
        
        metric.innerHTML = `
            <div class="metric-label">${formatLabel(key)}</div>
            <div class="metric-value">${value.close || value.level || 'N/A'}</div>
            ${value.change ? `<div class="metric-change ${changeClass}">${value.change}</div>` : ''}
        `;
        
        metricsGrid.appendChild(metric);
    });
    
    card.querySelector('.card-content').appendChild(metricsGrid);
    return card;
}

function renderKeyLevels(levels) {
    const card = createCard('🎯', 'Key Levels for Swing Traders');
    const content = card.querySelector('.card-content');
    
    const levelsList = document.createElement('div');
    levelsList.className = 'metrics-grid';
    
    const levelData = [
        { label: 'Support', value: levels.support },
        { label: 'Resistance', value: levels.resistance },
        { label: '20-day MA', value: levels.ma_20 },
        { label: '50-day MA', value: levels.ma_50 }
    ];
    
    levelData.forEach(item => {
        if (item.value) {
            const metric = document.createElement('div');
            metric.className = 'metric-item';
            metric.innerHTML = `
                <div class="metric-label">${item.label}</div>
                <div class="metric-value">${item.value}</div>
            `;
            levelsList.appendChild(metric);
        }
    });
    
    content.appendChild(levelsList);
    return card;
}

function renderIntradayLevels(levels) {
    const card = createCard('📈', 'Intraday Reference Levels');
    const content = card.querySelector('.card-content');
    
    const html = `
        <ul>
            <li><strong>Yesterday's Range:</strong> ${levels.yesterday_low} - ${levels.yesterday_high}</li>
            <li><strong>Yesterday's Close:</strong> ${levels.yesterday_close}</li>
            <li><strong>ATR (14-day):</strong> ${levels.atr} points (${levels.atr_pct})</li>
            <li><strong>Expected Today's Range:</strong> ${levels.expected_low} - ${levels.expected_high}</li>
            ${levels.gap_pct ? `<li><strong>Opening Gap:</strong> ${levels.gap_direction} ${levels.gap_pct}</li>` : ''}
        </ul>
    `;
    
    content.innerHTML = html;
    return card;
}

function renderBreadth(breadth) {
    const card = createCard('📊', 'Market Breadth');
    const content = card.querySelector('.card-content');
    
    const html = `
        <p><strong>Tone:</strong> ${breadth.tone}</p>
        <ul>
            <li><strong>${breadth.pct_above_50ma}</strong> of stocks above 50-day MA</li>
            <li><strong>Advance/Decline:</strong> ${breadth.advancing}/${breadth.declining} (ratio: ${breadth.ad_ratio})</li>
            <li><strong>Breadth Score:</strong> ${breadth.breadth_score}/100</li>
        </ul>
    `;
    
    content.innerHTML = html;
    return card;
}

function renderSentiment(sentiment) {
    const card = createCard('😰', 'Market Sentiment');
    const content = card.querySelector('.card-content');
    
    const score = parseInt(sentiment.score);
    
    const html = `
        <p><strong>CNN Fear & Greed Index:</strong> ${sentiment.score}/100 (${sentiment.interpretation}) ${sentiment.trend || ''}</p>
        ${sentiment.proxy ? '<p style="font-size: 13px; color: var(--text-tertiary);">[VIX-based proxy]</p>' : ''}
        <div class="sentiment-bar">
            <div class="sentiment-fill" style="width: ${score}%"></div>
            <div class="sentiment-label">${score}/100</div>
        </div>
        <p><strong>Signal:</strong> ${sentiment.signal}</p>
    `;
    
    content.innerHTML = html;
    return card;
}

function renderMarketContext(context) {
    const card = createCard('🔍', 'Market Context');
    const content = card.querySelector('.card-content');
    
    const html = `
        <ul>
            <li><strong>5-Day Trend:</strong> ${context.five_day_trend}</li>
            <li><strong>Week-to-Date:</strong> ${context.wtd}</li>
            <li><strong>MA Structure:</strong> ${context.ma_structure}</li>
            <li><strong>Volume:</strong> ${context.volume}</li>
        </ul>
    `;
    
    content.innerHTML = html;
    return card;
}

function renderSection(title, content) {
    const iconMap = {
        'Overnight Tone': '🌙',
        'What to Watch Today': '👀',
        'Pre-Market Movers': '🚀',
        'Swing-Trader Intention': '🎯',
        'Action Plan': '📋',
        'One-Line Game Plan': '⚡',
        'Tone of Today\'s Session': '📊',
        'What Drove Today\'s Moves': '💡',
        'Sector Leadership & Volatility': '📈',
        'Swing-Trader Reflection': '🤔',
        'Tomorrow\'s Setups': '🔮',
        'One-Sentence Takeaway': '💭'
    };
    
    const icon = iconMap[title] || '📄';
    const card = createCard(icon, title);
    const cardContent = card.querySelector('.card-content');
    
    // Format content (convert newlines to paragraphs)
    const formattedContent = formatContent(content);
    cardContent.innerHTML = formattedContent;
    
    return card;
}

function renderRSLeaders(leaders) {
    const card = createCard('⭐', 'Relative Strength Leaders');
    const content = card.querySelector('.card-content');
    
    if (!leaders || leaders.length === 0) {
        content.innerHTML = '<p>No stocks currently meet RS criteria</p>';
        return card;
    }
    
    const html = leaders.map((stock, index) => `
        <div class="metric-item" style="margin-bottom: 16px;">
            <div class="metric-label">${index + 1}. ${stock.ticker} ($${stock.price})</div>
            <div class="metric-value">RS Score: ${stock.rs_score}/100</div>
            <ul style="margin-top: 8px; font-size: 14px;">
                <li>20-Day: +${stock.stock_return}% (vs SPX: +${stock.relative_perf}%)</li>
                <li>Distance from 52w High: ${stock.pct_from_high}%</li>
                <li>Volume: ${stock.vol_increase >= 0 ? '+' : ''}${stock.vol_increase}% vs 10-day avg</li>
            </ul>
        </div>
    `).join('');
    
    content.innerHTML = html;
    return card;
}

function renderChecklist(checklist) {
    const card = createCard('✅', 'Swing Trade Checklist');
    const content = card.querySelector('.card-content');
    
    const html = `
        <p><strong>Rating:</strong> ${checklist.rating} (${checklist.interpretation})</p>
        <ul>
            ${checklist.items.map(item => `<li>${item}</li>`).join('')}
        </ul>
    `;
    
    content.innerHTML = html;
    return card;
}

// ===================================
// Utility Functions
// ===================================
function createCard(icon, title) {
    const card = document.createElement('div');
    card.className = 'card';
    
    card.innerHTML = `
        <div class="card-title">
            <span class="card-icon">${icon}</span>
            ${title}
        </div>
        <div class="card-content"></div>
    `;
    
    return card;
}

function formatSectionTitle(key) {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function formatLabel(key) {
    return key
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

function formatContent(content) {
    if (typeof content === 'object') {
        return Object.entries(content)
            .map(([key, value]) => `<p><strong>${formatLabel(key)}:</strong> ${value}</p>`)
            .join('');
    }
    
    // Convert line breaks to paragraphs
    return content
        .split('\n\n')
        .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
        .join('');
}

// ===================================
// Scroll to Top
// ===================================
function initializeScrollTop() {
    const scrollTopBtn = document.getElementById('scrollTop');
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('visible');
        } else {
            scrollTopBtn.classList.remove('visible');
        }
    });
    
    scrollTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}
