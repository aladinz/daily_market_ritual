CNN Fear & Greed Index - Composite sentiment
Why: Helps identify oversold/overbought conditions for reversals# Daily Market Ritual System

A production-ready Python system that auto-generates pre-market and post-market summaries using live market data, featuring a beautiful web dashboard for GitHub Pages deployment.

## 🌟 Features

### Core Analytics Engine
- ✅ **Pre-Market & Post-Market Reports** - Dual-mode ritual generation
- ✅ **Real-Time Market Data** - S&P 500, Nasdaq, Dow Jones, VIX from Yahoo Finance
- ✅ **Sector Tracking** - 11 sector ETFs for comprehensive coverage
- ✅ **Relative Strength Analysis** - Top 3 RS leaders vs SPX
- ✅ **Market Breadth** - A/D ratio, % above 50-MA, breadth score
- ✅ **Sentiment Analysis** - Fear & Greed Index integration
- ✅ **Key Levels** - Support, resistance, 20/50-day MAs
- ✅ **Intraday Levels** - ATR-based expected ranges
- ✅ **Swing Trade Checklist** - 10-point rating system

### New Dashboard Features
- 🎨 **Modern Web Dashboard** - Beautiful, responsive design
- 🌓 **Dark/Light Theme** - Auto-detection with manual toggle
- ⏰ **Smart Time Detection** - Auto-selects pre/post market based on CST time
- 👀 **What to Watch Tomorrow** - After-hours earnings, economic calendar, gap analysis
- 🚀 **Key Movers** - After-hours price action with catalysts
- 📊 **Enhanced Card Formatting** - Special styling for Tone, Catalysts, Sectors, Reflection, Takeaway
- 📱 **Mobile-Friendly** - Fully responsive design
- 🔄 **Auto-Updates** - PowerShell script for daily automation

## 📦 Installation

1. Clone the repository:
```powershell
git clone https://github.com/aladinz/daily_market_ritual.git
cd daily_market_ritual
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

Or with virtual environment:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 🚀 Usage

### Generate Market Ritual

**Auto-detect mode** (based on time):
```powershell
python market_ritual.py
```

**Pre-market mode** (before market open):
```powershell
python market_ritual.py --premarket
```

**Post-market mode** (after market close):
```powershell
python market_ritual.py --postmarket
```

### Convert to JSON for Dashboard

```powershell
python convert_to_json.py
```

### Update Dashboard (All-in-One)

```powershell
.\update_dashboard.ps1
```

This will:
1. Run market ritual (auto-detect mode)
2. Convert to JSON
3. Commit changes
4. Push to GitHub
5. Dashboard auto-updates in 2-3 minutes

## 🎨 Dashboard Deployment

### Live Dashboard
Once GitHub Pages is enabled, your dashboard will be live at:
```
https://aladinz.github.io/daily_market_ritual/dashboard/
```

### Enable GitHub Pages
1. Go to: `https://github.com/aladinz/daily_market_ritual/settings/pages`
2. Source: Deploy from a branch
3. Branch: main
4. Folder: / (root)
5. Click Save

### Local Testing
```powershell
cd dashboard
python -m http.server 8000
```
Then open: `http://localhost:8000`

## 📊 Report Sections

### Market Snapshot
- Index performance (SP500, Nasdaq, Dow, VIX)
- Key support/resistance levels
- Moving averages (20-day, 50-day)

### Intraday Reference Levels
- Yesterday's high/low/close
- ATR (Average True Range)
- Expected today's range

### Market Breadth
- % of stocks above 50-day MA
- Advance/Decline ratio
- Breadth score (0-100)

### Sentiment Analysis
- Fear & Greed Index
- VIX-based proxy
- Market signals

### Relative Strength Leaders
- Top 3 stocks outperforming SPX
- 20-day RS score (0-100)
- Distance from 52-week highs
- Volume confirmation

### What to Watch Tomorrow
- 📊 After-hours earnings reactions
- 📅 Economic calendar (CPI, PPI, Fed Decisions, NFP)
- 📈 Gap watch analysis
- 🔄 Sector rotation watch

### Key Movers
- After-hours price action
- Significant moves (±1% threshold)
- Smart catalyst detection
- Real-time updates

### Swing Trade Checklist
- 10-point checklist with rating
- Trend structure
- VIX levels
- Sector leadership
- Volume analysis
- 5-day trend

## 🛠️ Customization

### Add Custom Tickers
Edit `market_ritual.py`:
```python
STOCK_UNIVERSE = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META',
    # Add your tickers here
]
```

### Modify Dashboard Colors
Edit `dashboard/css/style.css`:
```css
:root {
    --accent: #4A90E2;  /* Your brand color */
    --success: #22C55E;
    --danger: #EF4444;
}
```

### Change Auto-Detection Times
Edit `dashboard/js/app.js`:
```javascript
if (totalMinutes < 660) { // 11:00 AM - adjust as needed
```

## ⏰ Automation

### PowerShell Script (Recommended)
```powershell
.\update_dashboard.ps1
```

### Windows Task Scheduler
Run daily at 4:30 PM ET:
```powershell
schtasks /create /tn "DailyMarketRitual" /tr "C:\Users\aladi\Daily_Market_Ritual\update_dashboard.ps1" /sc daily /st 16:30
```

For pre-market, schedule at 7:00 AM ET.

## 📁 Project Structure

```
Daily_Market_Ritual/
├── market_ritual.py           # Main Python ritual engine
├── convert_to_json.py         # JSON converter for dashboard
├── update_dashboard.ps1       # Automation script (all-in-one)
├── cleanup_old_reports.ps1    # Report cleanup utility
├── run_premarket.bat          # Pre-market batch file
├── run_postmarket.bat         # Post-market batch file
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── DEPLOYMENT.md              # Deployment guide
├── DASHBOARD_COMPLETE.md      # Dashboard documentation
│
├── dashboard/                 # Web dashboard
│   ├── index.html            # Main HTML
│   ├── css/style.css         # Styling with themes
│   ├── js/app.js             # Application logic
│   ├── data/                 # JSON data files
│   │   ├── premarket.json
│   │   └── postmarket.json
│   └── README.md             # Dashboard docs
│
└── rituals/                   # Generated reports
    ├── premarket/
    │   ├── latest.txt        # Current pre-market report
    │   └── summary_*.txt     # Historical reports
    └── postmarket/
        ├── latest.txt        # Current post-market report
        └── summary_*.txt     # Historical reports
```

## 🎯 Data Sources

- **Market Data**: Yahoo Finance API
- **Indices**: ^GSPC, ^IXIC, ^DJI, ^VIX
- **Sectors**: 11 Sector SPDR ETFs (XLK, XLF, XLV, XLE, XLY, XLI, XLP, XLU, XLB, XLRE, XLC)
- **Sentiment**: Fear & Greed Index (with VIX-based fallback)
- **Stock Universe**: 50+ high-quality, liquid names

## 🐛 Troubleshooting

### Dashboard Not Loading
- Check JSON files exist in `dashboard/data/`
- Verify JSON syntax (no errors)
- Check browser console (F12)

### Data Not Updating
- Verify `update_dashboard.ps1` ran successfully
- Check git push completed
- Wait 2-3 minutes for GitHub Pages rebuild
- Clear browser cache (Ctrl+Shift+R)

### "Unable to Load Data" Error
- Ensure JSON files are valid
- Check file paths are correct
- Verify repository is public (for GitHub Pages)

## 📈 Advanced Features

### Economic Calendar
Automatically tracks major events:
- CPI/PPI releases (8:30 AM ET)
- Fed Decisions (2:00 PM ET)
- NFP Jobs Report (8:30 AM ET)
- Weekly Jobless Claims (Thursdays 8:30 AM ET)

### Smart Gap Analysis
- Analyzes close position in daily range
- Predicts gap up/down potential
- Based on technical structure

### After-Hours Tracking
Monitors 10 major tickers:
- AAPL, MSFT, GOOGL, AMZN, NVDA
- TSLA, META, AMD, NFLX, CRM

## 🗂️ Report Management

As reports accumulate over time, use the cleanup utility to manage storage:

### Cleanup Old Reports

**Manual Cleanup**
```powershell
# Keep last 30 days, delete older reports
.\cleanup_old_reports.ps1

# Keep last 60 days
.\cleanup_old_reports.ps1 -DaysToKeep 60

# Keep last 30 days, archive (not delete) older ones
.\cleanup_old_reports.ps1 -Archive
```

**Automated Monthly Cleanup**

Add to Windows Task Scheduler for automatic maintenance:

1. **Task Name**: Monthly Report Cleanup
2. **Trigger**: First day of month at 6:00 AM
3. **Program**: `powershell.exe`
4. **Arguments**: `-ExecutionPolicy Bypass -File "C:\Users\aladi\Daily_Market_Ritual\cleanup_old_reports.ps1" -DaysToKeep 30`
5. **Run whether user is logged on or not**: Enabled

**What Gets Cleaned**
- ✅ Keeps `latest.txt` files (always preserved)
- ✅ Keeps reports from last N days
- ✅ Archives or deletes older timestamped reports (`summary_*.txt`)
- ✅ Works on both `premarket` and `postmarket` folders
- ✅ Safe - only targets old summary files

**Recommended Settings**
- **Active Trading**: Keep 30 days (1 month of history)
- **Long-term Analysis**: Keep 60-90 days (3 months)
- **Archive Mode**: Use `-Archive` flag for first run to be safe

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

MIT License - Free to use and modify

## 🎊 Credits

Market Ritual Dashboard Made with ❤️ By Aladdin for Traders.

---

**For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**  
**For dashboard documentation, see [DASHBOARD_COMPLETE.md](DASHBOARD_COMPLETE.md)**
