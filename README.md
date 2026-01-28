# Daily Market Ritual System

A production-ready Python tool that auto-generates post-market summaries using live market data from Yahoo Finance.

## Features

- ✅ Fetches real-time data for S&P 500, Nasdaq, Dow Jones, and VIX
- ✅ Tracks 11 sector ETFs for comprehensive market coverage
- ✅ Analyzes market tone (risk-on, risk-off, mixed)
- ✅ Identifies sector leaders and laggards
- ✅ Provides swing-trader reflection insights
- ✅ Saves formatted summaries to `~/rituals/post_market/latest.txt`
- ✅ Archives each run with timestamps

## Installation

1. Install dependencies:
```powershell
pip install -r requirements.txt
```

Or if using the virtual environment:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Usage

Run the daily ritual script:

```powershell
python market_ritual.py
```

Or with virtual environment:
```powershell
.venv\Scripts\python.exe market_ritual.py
```

The script will:
1. Fetch live market data from Yahoo Finance
2. Analyze indices, sectors, and volatility
3. Generate a comprehensive post-market summary
4. Save to both `~/rituals/post_market/latest.txt` and `rituals/post_market/latest.txt`
5. Create a timestamped archive in `rituals/post_market/`

## Output

The generated summary includes:

1. **Market Close Snapshot** - Index performance with % changes
2. **Tone of Today's Session** - Overall market sentiment analysis
3. **What Drove Today's Moves** - Macro, earnings, and headline analysis
4. **Sector Leadership & Volatility** - Top/bottom sectors and VIX analysis
5. **Swing-Trader Reflection** - Actionable insights for traders
6. **Portfolio & Watchlist** - Placeholders for manual entry
7. **One-Sentence Takeaway** - Quick summary

## Data Sources

- **Indices**: Yahoo Finance (^GSPC, ^IXIC, ^DJI, ^VIX)
- **Sectors**: 11 Sector SPDR ETFs (XLK, XLF, XLV, XLE, XLY, XLI, XLP, XLU, XLB, XLRE, XLC)

## Customization

Edit `market_ritual.py` to:
- Add more indices or ETFs
- Modify analysis logic
- Customize the output template
- Change save locations

## Automation

To run this daily automatically:

**Windows Task Scheduler:**
```powershell
# Create a scheduled task to run at 4:30 PM ET daily
schtasks /create /tn "DailyMarketRitual" /tr "C:\Users\aladi\Daily_Market_Ritual\.venv\Scripts\python.exe C:\Users\aladi\Daily_Market_Ritual\market_ritual.py" /sc daily /st 16:30
```

**Or use a simple batch file:**
Create `run_ritual.bat`:
```batch
@echo off
cd /d C:\Users\aladi\Daily_Market_Ritual
.venv\Scripts\python.exe market_ritual.py
pause
```

## Requirements

- Python 3.7+
- Internet connection for live data
- Dependencies: yfinance, pandas, numpy, requests, python-dateutil

## License

MIT License - Free to use and modify
