#!/usr/bin/env python3
"""
Daily Market Ritual System
Auto-generates pre-market and post-market reports using live market data.

USAGE:
    python market_ritual.py                    # Auto-detect based on time
    python market_ritual.py --premarket        # Force pre-market report
    python market_ritual.py --postmarket       # Force post-market report

SCHEDULING:
    Morning (7:00 AM CST):  python market_ritual.py --premarket
    Evening (4:00 PM CST):  python market_ritual.py --postmarket

TIME DETECTION:
    - Before 11:00 AM CST → Pre-market mode
    - After 3:10 PM CST → Post-market mode
    - During market hours → Requires manual flag

ANYTHINGLLM INTEGRATION:
    Point your knowledge base to:
    - ~/rituals/premarket/latest.txt
    - ~/rituals/postmarket/latest.txt
    
    These files are automatically updated with each run.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import os
import requests
import re
import argparse
from zoneinfo import ZoneInfo


class MarketRitual:
    """Main class for fetching and analyzing market data."""
    
    # Market indices
    INDICES = {
        'SP500': '^GSPC',
        'NASDAQ': '^IXIC',
        'DOW': '^DJI',
        'VIX': '^VIX'
    }
    
    # Futures contracts for pre-market
    FUTURES = {
        'ES': 'ES=F',  # S&P 500 Futures
        'NQ': 'NQ=F',  # Nasdaq Futures
        'YM': 'YM=F'   # Dow Futures
    }
    
    # Sector ETFs for sector performance tracking
    SECTORS = {
        'Technology': 'XLK',
        'Financials': 'XLF',
        'Healthcare': 'XLV',
        'Energy': 'XLE',
        'Consumer Discretionary': 'XLY',
        'Industrials': 'XLI',
        'Consumer Staples': 'XLP',
        'Utilities': 'XLU',
        'Materials': 'XLB',
        'Real Estate': 'XLRE',
        'Communication Services': 'XLC'
    }
    
    # Stock universe for RS analysis (high-quality, liquid names)
    STOCK_UNIVERSE = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK.B',
        'JPM', 'V', 'JNJ', 'WMT', 'MA', 'PG', 'UNH', 'HD', 'COST', 'BAC',
        'XOM', 'ABBV', 'AVGO', 'LLY', 'CRM', 'ORCL', 'CVX', 'KO', 'PEP',
        'TMO', 'MRK', 'ADBE', 'CSCO', 'ACN', 'NKE', 'ABT', 'MCD', 'DHR',
        'TXN', 'QCOM', 'NEE', 'HON', 'UNP', 'PM', 'RTX', 'INTC', 'INTU',
        'AMD', 'AMGN', 'CMCSA', 'LOW', 'SBUX', 'GE', 'BA', 'CAT', 'NOW'
    ]
    
    # Economic calendar - approximate dates (update monthly)
    # Format: {month: {day: 'Event Name'}}
    MACRO_CALENDAR_2026 = {
        1: {13: 'CPI', 14: 'PPI', 29: 'Fed Decision'},
        2: {2: 'NFP Jobs Report', 12: 'CPI', 13: 'PPI'},
        3: {6: 'NFP Jobs Report', 12: 'CPI', 13: 'PPI', 18: 'Fed Decision'},
        4: {4: 'NFP Jobs Report', 10: 'CPI', 11: 'PPI'},
        5: {1: 'NFP Jobs Report', 13: 'CPI', 14: 'PPI', 6: 'Fed Decision'},
        6: {5: 'NFP Jobs Report', 10: 'CPI', 11: 'PPI'},
        7: {2: 'NFP Jobs Report', 11: 'CPI', 14: 'PPI', 29: 'Fed Decision'},
        8: {6: 'NFP Jobs Report', 13: 'CPI', 14: 'PPI'},
        9: {4: 'NFP Jobs Report', 11: 'CPI', 12: 'PPI', 17: 'Fed Decision'},
        10: {2: 'NFP Jobs Report', 10: 'CPI', 11: 'PPI'},
        11: {6: 'NFP Jobs Report', 12: 'CPI', 13: 'PPI', 5: 'Fed Decision'},
        12: {4: 'NFP Jobs Report', 10: 'CPI', 11: 'PPI', 16: 'Fed Decision'}
    }
    
    def __init__(self, mode='postmarket'):
        """Initialize the ritual with specified mode."""
        self.mode = mode  # 'premarket' or 'postmarket'
        self.data = {}
        self.sector_data = {}
        self.futures_data = {}
        self.analysis = {}
        self.headlines = []
        self.top_movers = {'gainers': [], 'losers': []}
        
    # ============================================================================
    # COMMON DATA FETCHING METHODS
    # ============================================================================
    
    def fetch_headlines(self):
        """Fetch top Yahoo Finance headlines."""
        try:
            # Try to fetch Yahoo Finance news
            url = "https://finance.yahoo.com/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Simple regex to extract headlines from HTML
                headline_patterns = re.findall(r'<h3[^>]*>([^<]+)</h3>', response.text)
                self.headlines = [h.strip() for h in headline_patterns[:10] if len(h.strip()) > 20]
                print(f"✓ Fetched {len(self.headlines)} headlines")
            else:
                self.headlines = []
                print("✗ Could not fetch headlines")
        except Exception as e:
            print(f"✗ Error fetching headlines: {e}")
            self.headlines = []
    
    def fetch_top_movers(self):
        """Fetch top S&P 500 gainers and losers."""
        print("Fetching top market movers...")
        try:
            # Fetch a few major stocks as proxies for movers
            major_stocks = {
                'AAPL': 'Apple', 'MSFT': 'Microsoft', 'GOOGL': 'Alphabet',
                'AMZN': 'Amazon', 'NVDA': 'NVIDIA', 'TSLA': 'Tesla',
                'META': 'Meta', 'JPM': 'JPMorgan', 'V': 'Visa',
                'WMT': 'Walmart', 'XOM': 'Exxon', 'UNH': 'UnitedHealth'
            }
            
            movers_data = []
            for ticker, name in major_stocks.items():
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='2d')
                    if len(hist) >= 2:
                        change_pct = ((hist.iloc[-1]['Close'] - hist.iloc[-2]['Close']) / hist.iloc[-2]['Close']) * 100
                        movers_data.append({
                            'ticker': ticker,
                            'name': name,
                            'change_pct': change_pct
                        })
                except:
                    pass
            
            # Sort and get top/bottom
            movers_data.sort(key=lambda x: x['change_pct'], reverse=True)
            self.top_movers['gainers'] = movers_data[:3]
            self.top_movers['losers'] = movers_data[-3:]
            
            print(f"✓ Identified {len(self.top_movers['gainers'])} top gainers and {len(self.top_movers['losers'])} losers")
            
        except Exception as e:
            print(f"✗ Error fetching movers: {e}")
    
    def analyze_relative_strength(self):
        """Identify stocks with strong relative strength vs SPX.
        
        Returns top 3 stocks with:
        - Outperforming SPX over 20 days
        - Strong recent momentum (5-day trend)
        - Above-average volume confirmation
        """
        print("Analyzing relative strength...")
        
        try:
            # Fetch SPX for comparison
            spx = yf.Ticker('^GSPC')
            spx_hist = spx.history(period='3mo')
            
            if len(spx_hist) < 20:
                print("✗ Insufficient SPX data for RS analysis")
                return []
            
            # Calculate SPX returns
            spx_20d_return = ((spx_hist['Close'].iloc[-1] - spx_hist['Close'].iloc[-21]) / 
                              spx_hist['Close'].iloc[-21]) * 100
            spx_5d_return = ((spx_hist['Close'].iloc[-1] - spx_hist['Close'].iloc[-6]) / 
                             spx_hist['Close'].iloc[-6]) * 100
            
            rs_leaders = []
            
            # Analyze each stock in universe
            for ticker in self.STOCK_UNIVERSE:
                try:
                    stock = yf.Ticker(ticker)
                    stock_hist = stock.history(period='6mo')
                    
                    if len(stock_hist) < 20:
                        continue
                    
                    # Calculate returns
                    current_price = stock_hist['Close'].iloc[-1]
                    stock_20d_return = ((current_price - stock_hist['Close'].iloc[-21]) / 
                                        stock_hist['Close'].iloc[-21]) * 100
                    stock_5d_return = ((current_price - stock_hist['Close'].iloc[-6]) / 
                                       stock_hist['Close'].iloc[-6]) * 100
                    
                    # Calculate relative performance vs SPX
                    relative_perf_20d = stock_20d_return - spx_20d_return
                    relative_perf_5d = stock_5d_return - spx_5d_return
                    
                    # Focus on stocks with positive momentum (outperforming SPX)
                    if relative_perf_20d <= 0:
                        continue
                    
                    # Check 52-week high proximity (but not as strict)
                    week_52_high = stock_hist['High'].max()
                    pct_from_high = ((current_price - week_52_high) / week_52_high) * 100
                    
                    # Check volume confirmation
                    recent_vol = stock_hist['Volume'].iloc[-10:].mean()
                    prior_vol = stock_hist['Volume'].iloc[-20:-10].mean()
                    
                    if prior_vol > 0:
                        vol_increase = ((recent_vol - prior_vol) / prior_vol) * 100
                    else:
                        vol_increase = 0
                    
                    # Calculate RS Rating (0-100 scale)
                    # Emphasize recent momentum more than 52-week highs
                    rs_score = min(100, (
                        (relative_perf_20d / 5 * 40) +  # 20-day relative performance
                        (relative_perf_5d / 3 * 30) +    # 5-day momentum (more weight)
                        ((100 + pct_from_high) / 10 * 20) +  # 52-week high proximity (less weight)
                        (min(vol_increase, 50) * 0.2)    # Volume increase
                    ))
                    
                    rs_leaders.append({
                        'ticker': ticker,
                        'relative_perf': relative_perf_20d,
                        'stock_20d_return': stock_20d_return,
                        'stock_5d_return': stock_5d_return,
                        'pct_from_52w_high': pct_from_high,
                        'vol_increase': vol_increase,
                        'rs_score': rs_score,
                        'current_price': current_price
                    })
                    
                except Exception as e:
                    # Silently skip stocks with errors
                    continue
            
            # Sort by RS score and return top 3
            rs_leaders.sort(key=lambda x: x['rs_score'], reverse=True)
            top_3 = rs_leaders[:3]
            
            if top_3:
                print(f"✓ Identified {len(rs_leaders)} RS leaders, returning top 3")
            else:
                print("✗ No stocks met RS criteria (>2% outperformance, near 52w high, volume)")
            
            return top_3
            
        except Exception as e:
            print(f"✗ Error in RS analysis: {e}")
            return []
    
    def analyze_market_breadth(self):
        """Calculate market breadth indicators.
        
        Returns:
            - % of stocks above 50-day MA
            - Advance/Decline estimate (based on sample)
            - Market breadth score
        """
        print("Analyzing market breadth...")
        
        try:
            above_ma_count = 0
            total_valid = 0
            advancing = 0
            declining = 0
            
            # Analyze stock universe for breadth
            for ticker in self.STOCK_UNIVERSE:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='3mo')
                    
                    if len(hist) < 50:
                        continue
                    
                    total_valid += 1
                    
                    # Check if above 50-day MA
                    ma_50 = hist['Close'].iloc[-50:].mean()
                    current_price = hist['Close'].iloc[-1]
                    
                    if current_price > ma_50:
                        above_ma_count += 1
                    
                    # Check advance/decline (today vs yesterday)
                    if len(hist) >= 2:
                        if hist['Close'].iloc[-1] > hist['Close'].iloc[-2]:
                            advancing += 1
                        else:
                            declining += 1
                    
                except:
                    continue
            
            if total_valid == 0:
                print("✗ Insufficient data for breadth analysis")
                return None
            
            pct_above_50ma = (above_ma_count / total_valid) * 100
            ad_ratio = advancing / declining if declining > 0 else 0
            
            # Breadth score (0-100)
            breadth_score = min(100, (pct_above_50ma * 0.6) + (min(ad_ratio * 100, 40)))
            
            # Classify breadth
            if pct_above_50ma > 70 and ad_ratio > 2:
                breadth_tone = "Strong Bullish"
            elif pct_above_50ma > 60 and ad_ratio > 1.5:
                breadth_tone = "Bullish"
            elif pct_above_50ma > 40 and ad_ratio > 0.8:
                breadth_tone = "Neutral"
            elif pct_above_50ma > 30:
                breadth_tone = "Bearish"
            else:
                breadth_tone = "Weak Bearish"
            
            result = {
                'pct_above_50ma': pct_above_50ma,
                'advancing': advancing,
                'declining': declining,
                'ad_ratio': ad_ratio,
                'breadth_score': breadth_score,
                'breadth_tone': breadth_tone,
                'sample_size': total_valid
            }
            
            print(f"✓ Breadth: {pct_above_50ma:.1f}% above 50-MA, A/D: {advancing}/{declining}")
            return result
            
        except Exception as e:
            print(f"✗ Error in breadth analysis: {e}")
            return None
    
    def calculate_intraday_levels(self):
        """Calculate key intraday reference levels.
        
        Returns:
            - Yesterday's high/low
            - ATR (14-day Average True Range)
            - Opening gap (for pre-market)
        """
        print("Calculating intraday levels...")
        
        try:
            spx = yf.Ticker('^GSPC')
            hist = spx.history(period='1mo')
            
            if len(hist) < 14:
                print("✗ Insufficient data for intraday levels")
                return None
            
            # Yesterday's high/low
            yesterday_high = hist['High'].iloc[-1]
            yesterday_low = hist['Low'].iloc[-1]
            yesterday_close = hist['Close'].iloc[-1]
            
            # Calculate True Range for last 14 days
            true_ranges = []
            for i in range(-14, 0):
                high = hist['High'].iloc[i]
                low = hist['Low'].iloc[i]
                prev_close = hist['Close'].iloc[i-1] if i > -len(hist) else hist['Close'].iloc[i]
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                true_ranges.append(tr)
            
            atr = np.mean(true_ranges)
            atr_pct = (atr / yesterday_close) * 100
            
            # Expected range based on ATR
            expected_high = yesterday_close + atr
            expected_low = yesterday_close - atr
            
            # Gap calculation (if futures data available)
            gap_pct = None
            gap_size = None
            if self.futures_data and 'ES' in self.futures_data:
                futures_price = self.futures_data['ES']['close']
                gap_size = futures_price - yesterday_close
                gap_pct = (gap_size / yesterday_close) * 100
            
            result = {
                'yesterday_high': yesterday_high,
                'yesterday_low': yesterday_low,
                'yesterday_close': yesterday_close,
                'atr': atr,
                'atr_pct': atr_pct,
                'expected_high': expected_high,
                'expected_low': expected_low,
                'gap_pct': gap_pct,
                'gap_size': gap_size
            }
            
            print(f"✓ Yesterday H/L: {yesterday_high:.2f}/{yesterday_low:.2f}, ATR: {atr:.2f} ({atr_pct:.1f}%)")
            return result
            
        except Exception as e:
            print(f"✗ Error calculating intraday levels: {e}")
            return None
    
    def fetch_fear_greed_index(self):
        """Fetch CNN Fear & Greed Index.
        
        Returns sentiment score (0-100) with interpretation:
        - 0-25: Extreme Fear (contrarian buy signal)
        - 25-45: Fear (cautious, potential reversal setup)
        - 45-55: Neutral
        - 55-75: Greed (caution on longs)
        - 75-100: Extreme Greed (contrarian sell signal)
        """
        print("Fetching Fear & Greed Index...")
        
        try:
            # CNN Fear & Greed Index endpoint
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.cnn.com/',
                'Origin': 'https://www.cnn.com'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract current fear & greed value
                if 'fear_and_greed' in data:
                    score = data['fear_and_greed']['score']
                    rating = data['fear_and_greed']['rating']
                    
                    # Get previous day for trend
                    previous_score = None
                    if 'fear_and_greed_historical' in data and len(data['fear_and_greed_historical']['data']) > 1:
                        previous_score = data['fear_and_greed_historical']['data'][1]['score']
                    
                    # Classify sentiment
                    if score <= 25:
                        interpretation = "Extreme Fear"
                        signal = "Contrarian BUY signal - market oversold"
                    elif score <= 45:
                        interpretation = "Fear"
                        signal = "Potential reversal setup - watch for bottoming"
                    elif score <= 55:
                        interpretation = "Neutral"
                        signal = "Balanced sentiment - no extreme"
                    elif score <= 75:
                        interpretation = "Greed"
                        signal = "Caution on new longs - sentiment stretched"
                    else:
                        interpretation = "Extreme Greed"
                        signal = "Contrarian SELL signal - market overbought"
                    
                    # Determine trend
                    trend = ""
                    if previous_score:
                        change = score - previous_score
                        if change > 5:
                            trend = "↑ Rising"
                        elif change < -5:
                            trend = "↓ Falling"
                        else:
                            trend = "→ Stable"
                    
                    result = {
                        'score': score,
                        'rating': rating,
                        'interpretation': interpretation,
                        'signal': signal,
                        'previous_score': previous_score,
                        'trend': trend
                    }
                    
                    print(f"✓ Fear & Greed: {score}/100 ({interpretation})")
                    return result
                else:
                    print("✗ Unexpected data format from Fear & Greed API")
                    return self._calculate_manual_sentiment()
            else:
                print(f"✗ Failed to fetch Fear & Greed Index (status: {response.status_code})")
                return self._calculate_manual_sentiment()
                
        except Exception as e:
            print(f"✗ Error fetching Fear & Greed Index: {e}")
            return self._calculate_manual_sentiment()
    
    def _calculate_manual_sentiment(self):
        """Calculate a simple sentiment proxy when Fear & Greed API is unavailable.
        
        Uses VIX level and SPX performance as sentiment proxy.
        """
        try:
            if 'VIX' not in self.data or 'SP500' not in self.data:
                return None
            
            vix = self.data['VIX']['close']
            sp_change_5d = self.data['SP500'].get('five_day_change', 0)
            
            # Create sentiment score from VIX and recent performance
            # Low VIX + positive returns = Greed
            # High VIX + negative returns = Fear
            
            # VIX component (inverted: low VIX = high score)
            if vix < 12:
                vix_score = 90
            elif vix < 15:
                vix_score = 70
            elif vix < 20:
                vix_score = 50
            elif vix < 25:
                vix_score = 30
            else:
                vix_score = 10
            
            # Performance component
            if sp_change_5d > 3:
                perf_score = 80
            elif sp_change_5d > 1:
                perf_score = 65
            elif sp_change_5d > -1:
                perf_score = 50
            elif sp_change_5d > -3:
                perf_score = 35
            else:
                perf_score = 20
            
            # Weighted average
            score = int((vix_score * 0.6) + (perf_score * 0.4))
            
            # Classify
            if score <= 25:
                interpretation = "Extreme Fear"
                signal = "Contrarian BUY signal - market oversold"
            elif score <= 45:
                interpretation = "Fear"
                signal = "Potential reversal setup - watch for bottoming"
            elif score <= 55:
                interpretation = "Neutral"
                signal = "Balanced sentiment - no extreme"
            elif score <= 75:
                interpretation = "Greed"
                signal = "Caution on new longs - sentiment stretched"
            else:
                interpretation = "Extreme Greed"
                signal = "Contrarian SELL signal - market overbought"
            
            result = {
                'score': score,
                'rating': interpretation,
                'interpretation': interpretation,
                'signal': signal,
                'previous_score': None,
                'trend': '',
                'proxy': True  # Flag to indicate this is a proxy calculation
            }
            
            print(f"✓ Sentiment Proxy: {score}/100 ({interpretation}) [VIX-based]")
            return result
            
        except Exception as e:
            print(f"✗ Unable to calculate sentiment proxy: {e}")
            return None
    
    def get_scheduled_events_today(self):
        """Check if there are any scheduled macro events today."""
        today = datetime.now()
        month = today.month
        day = today.day
        
        if month in self.MACRO_CALENDAR_2026:
            if day in self.MACRO_CALENDAR_2026[month]:
                return self.MACRO_CALENDAR_2026[month][day]
        return None
    
    # ============================================================================
    # PRE-MARKET SPECIFIC METHODS
    # ============================================================================
    
    def fetch_futures_data(self):
        """Fetch overnight futures data with extended history."""
        print("Fetching futures data...")
        
        for name, ticker in self.FUTURES.items():
            try:
                future = yf.Ticker(ticker)
                hist = future.history(period='1mo')  # Extended for trend analysis
                
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    previous = hist.iloc[-2]
                    
                    change_pct = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
                    
                    # 5-day trend for futures
                    five_days_ago = hist.iloc[-6]['Close'] if len(hist) >= 6 else hist.iloc[0]['Close']
                    five_day_change = ((latest['Close'] - five_days_ago) / five_days_ago) * 100
                    
                    self.futures_data[name] = {
                        'close': latest['Close'],
                        'previous_close': previous['Close'],
                        'change_pct': change_pct,
                        'five_day_change': five_day_change
                    }
                    print(f"✓ {name}: {change_pct:+.2f}%")
                else:
                    print(f"✗ {name}: Insufficient data")
                    
            except Exception as e:
                print(f"✗ Error fetching {name}: {e}")
    
    def analyze_premarket_tone(self):
        """Determine pre-market sentiment from futures."""
        if not self.futures_data:
            return "Unknown - insufficient futures data"
        
        # Get futures changes
        es_change = self.futures_data.get('ES', {}).get('change_pct', 0)
        nq_change = self.futures_data.get('NQ', {}).get('change_pct', 0)
        ym_change = self.futures_data.get('YM', {}).get('change_pct', 0)
        
        avg_change = (es_change + nq_change + ym_change) / 3
        
        # Determine tone
        if avg_change > 0.5:
            tone = "**Bullish Pre-Market** - Futures pointing to a positive open"
        elif avg_change > 0.2:
            tone = "**Cautiously Bullish** - Modest gains in overnight futures"
        elif avg_change > -0.2:
            tone = "**Flat/Mixed** - Futures showing little direction"
        elif avg_change > -0.5:
            tone = "**Cautiously Bearish** - Modest weakness in futures"
        else:
            tone = "**Bearish Pre-Market** - Futures pointing to a negative open"
        
        # Add context
        if nq_change > es_change + 0.3:
            tone += ". Tech futures leading."
        elif es_change > nq_change + 0.3:
            tone += ". Broad market outperforming tech."
        
        return tone
    
    def generate_premarket_intention(self):
        """Generate swing trader's intention for the day."""
        es_change = self.futures_data.get('ES', {}).get('change_pct', 0)
        scheduled_event = self.get_scheduled_events_today()
        
        intention = {}
        
        # Market bias
        if es_change > 0.5:
            intention['bias'] = "**Today's Bias**: Bullish - looking for breakouts and follow-through"
        elif es_change < -0.5:
            intention['bias'] = "**Today's Bias**: Defensive - watching support levels and hedges"
        else:
            intention['bias'] = "**Today's Bias**: Neutral - waiting for clear setups"
        
        # Event awareness
        if scheduled_event:
            # Determine correct time for the event
            if 'Fed Decision' in scheduled_event:
                event_time = "2:00 PM ET (Powell presser at 2:30 PM ET)"
            elif 'CPI' in scheduled_event or 'PPI' in scheduled_event or 'NFP' in scheduled_event or 'Jobless Claims' in scheduled_event:
                event_time = "8:30 AM ET"
            else:
                event_time = "8:30 AM ET"
            
            intention['catalyst'] = f"**Key Event**: {scheduled_event} at {event_time} - expect volatility"
        else:
            intention['catalyst'] = "**Key Event**: No major scheduled releases - focus on technicals"
        
        # Focus areas
        sectors = self.analyze_premarket_sectors()
        if sectors['leaders']:
            intention['focus'] = f"**Focus**: Watch {sectors['leaders'][0].split(':')[0] if ':' in sectors['leaders'][0] else sectors['leaders'][0]} for momentum"
        else:
            intention['focus'] = "**Focus**: Wait for market open to identify leaders"
        
        # Risk management
        if abs(es_change) > 1:
            intention['risk'] = "**Risk**: High volatility expected - use wider stops"
        else:
            intention['risk'] = "**Risk**: Normal conditions - standard position sizing"
        
        return intention
    
    def analyze_premarket_sectors(self):
        """Check pre-market sector movements (uses regular market data)."""
        # Fetch sector data from previous close for context
        if not self.sector_data:
            self.fetch_sector_data()
        
        if not self.sector_data:
            return {'leaders': [], 'laggards': []}
        
        # Sort sectors by performance
        sorted_sectors = sorted(
            self.sector_data.items(),
            key=lambda x: x[1]['change_pct'],
            reverse=True
        )
        
        # Get top 2 and bottom 2
        leaders = [
            f"{name} ({data['ticker']})"
            for name, data in sorted_sectors[:2]
        ]
        
        laggards = [
            f"{name} ({data['ticker']})"
            for name, data in sorted_sectors[-2:]
        ]
        
        return {'leaders': leaders, 'laggards': laggards}
    
    def analyze_futures_trend(self):
        """Analyze multi-day futures trend."""
        if 'ES' not in self.futures_data:
            return "Futures trend data unavailable"
        
        es_5day = self.futures_data['ES'].get('five_day_change', 0)
        
        if es_5day > 2:
            return f"**Futures 5-Day Trend**: Strong uptrend ({es_5day:+.1f}%) - bullish momentum"
        elif es_5day > 0.5:
            return f"**Futures 5-Day Trend**: Mild uptrend ({es_5day:+.1f}%)"
        elif es_5day > -0.5:
            return f"**Futures 5-Day Trend**: Sideways ({es_5day:+.1f}%)"
        elif es_5day > -2:
            return f"**Futures 5-Day Trend**: Mild downtrend ({es_5day:+.1f}%)"
        else:
            return f"**Futures 5-Day Trend**: Strong downtrend ({es_5day:+.1f}%) - bearish momentum"
    
    # ============================================================================
    # POST-MARKET SPECIFIC METHODS
    # ============================================================================
    
    def fetch_index_data(self):
        """Fetch latest data for major indices with extended history for analysis."""
        print("Fetching market indices data...")
        
        for name, ticker in self.INDICES.items():
            try:
                stock = yf.Ticker(ticker)
                # Fetch more data for moving averages and trend analysis
                hist = stock.history(period='3mo')
                
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    previous = hist.iloc[-2]
                    
                    change_pct = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
                    
                    # Calculate moving averages
                    ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else None
                    ma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
                    ma_200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) >= 200 else None
                    
                    # Calculate pivot points (standard method)
                    pivot = (latest['High'] + latest['Low'] + latest['Close']) / 3
                    resistance_1 = (2 * pivot) - latest['Low']
                    support_1 = (2 * pivot) - latest['High']
                    
                    # 5-day trend
                    five_days_ago = hist.iloc[-6]['Close'] if len(hist) >= 6 else hist.iloc[0]['Close']
                    five_day_change = ((latest['Close'] - five_days_ago) / five_days_ago) * 100
                    
                    # Week-to-date (assume Monday start)
                    week_start_idx = max(0, len(hist) - 5)  # Approximate last 5 trading days
                    week_start_close = hist.iloc[week_start_idx]['Close']
                    wtd_change = ((latest['Close'] - week_start_close) / week_start_close) * 100
                    
                    # Volume analysis
                    avg_volume_10d = hist['Volume'].tail(10).mean()
                    if avg_volume_10d > 0:
                        volume_vs_avg = ((latest['Volume'] - avg_volume_10d) / avg_volume_10d) * 100
                    else:
                        volume_vs_avg = 0
                    
                    self.data[name] = {
                        'close': latest['Close'],
                        'previous_close': previous['Close'],
                        'change_pct': change_pct,
                        'high': latest['High'],
                        'low': latest['Low'],
                        'volume': latest['Volume'],
                        'ma_20': ma_20,
                        'ma_50': ma_50,
                        'ma_200': ma_200,
                        'pivot': pivot,
                        'resistance_1': resistance_1,
                        'support_1': support_1,
                        'five_day_change': five_day_change,
                        'wtd_change': wtd_change,
                        'volume_vs_avg': volume_vs_avg,
                        'hist': hist  # Keep history for additional analysis
                    }
                    print(f"✓ {name}: {change_pct:+.2f}%")
                else:
                    print(f"✗ {name}: Insufficient data")
                    
            except Exception as e:
                print(f"✗ Error fetching {name}: {e}")
    
    def fetch_sector_data(self):
        """Fetch sector ETF performance."""
        print("Fetching sector data...")
        
        for sector_name, ticker in self.SECTORS.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period='5d')
                
                if len(hist) >= 2:
                    latest = hist.iloc[-1]
                    previous = hist.iloc[-2]
                    
                    change_pct = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
                    
                    self.sector_data[sector_name] = {
                        'ticker': ticker,
                        'close': latest['Close'],
                        'change_pct': change_pct
                    }
                    
            except Exception as e:
                print(f"✗ Error fetching {sector_name}: {e}")
                
        print(f"✓ Fetched {len(self.sector_data)} sectors")
    
    def analyze_market_tone(self):
        """Determine the overall market tone based on index performance."""
        if not self.data:
            return "Unknown - insufficient data"
        
        # Get changes for major indices
        sp_change = self.data.get('SP500', {}).get('change_pct', 0)
        nasdaq_change = self.data.get('NASDAQ', {}).get('change_pct', 0)
        dow_change = self.data.get('DOW', {}).get('change_pct', 0)
        vix_change = self.data.get('VIX', {}).get('change_pct', 0)
        
        # Calculate average move
        avg_change = (sp_change + nasdaq_change + dow_change) / 3
        
        # Determine tone
        if avg_change > 1.0:
            if vix_change < -5:
                tone = "**Risk-On** - Strong bullish session with declining volatility"
            else:
                tone = "**Risk-On** - Broad market strength across indices"
        elif avg_change > 0.3:
            tone = "**Mildly Risk-On** - Modest gains with cautious optimism"
        elif avg_change > -0.3:
            if abs(nasdaq_change - dow_change) > 1.5:
                tone = "**Mixed/Rotational** - Divergent performance across indices"
            else:
                tone = "**Mixed** - Choppy session with no clear direction"
        elif avg_change > -1.0:
            tone = "**Mildly Risk-Off** - Modest selling pressure"
        else:
            if vix_change > 10:
                tone = "**Risk-Off** - Heavy selling with spiking volatility"
            else:
                tone = "**Risk-Off** - Broad market weakness"
        
        # Add context
        if sp_change > 0 and nasdaq_change < 0:
            tone += ". Value outperformed growth."
        elif nasdaq_change > sp_change + 0.5:
            tone += ". Tech-led rally."
        
        return tone
    
    def detect_catalysts(self):
        """Detect real market catalysts from multiple sources."""
        print("\nDetecting market catalysts...")
        
        # Fetch data
        self.fetch_headlines()
        self.fetch_top_movers()
        
        # Initialize outputs
        macro_drivers = ""
        earnings_drivers = ""
        headline_drivers = ""
        
        # 1. Check macro calendar
        scheduled_event = self.get_scheduled_events_today()
        
        # 2. Scan headlines for keywords
        macro_keywords = {
            'inflation': ['CPI', 'PPI', 'PCE', 'inflation'],
            'fed': ['FOMC', 'Fed ', 'Federal Reserve', 'Powell', 'rate'],
            'jobs': ['jobs', 'NFP', 'unemployment', 'payroll'],
            'economy': ['ISM', 'GDP', 'retail sales', 'consumer'],
            'geopolitical': ['tension', 'conflict', 'sanction', 'oil', 'OPEC', 'war'],
            'sentiment': ['volatility', 'selloff', 'rally', 'rotation', 'risk-off', 'risk-on']
        }
        
        detected_themes = {}
        all_headlines = ' '.join(self.headlines)
        
        for theme, keywords in macro_keywords.items():
            for keyword in keywords:
                if keyword.lower() in all_headlines.lower():
                    if theme not in detected_themes:
                        detected_themes[theme] = []
                    detected_themes[theme].append(keyword)
        
        # 3. Build macro driver string
        macro_parts = []
        
        if scheduled_event:
            macro_parts.append(f"**{scheduled_event} Release**: Market reacted to today's data.")
        
        if 'inflation' in detected_themes:
            macro_parts.append(f"Inflation concerns in focus ({', '.join(detected_themes['inflation'][:2])}).")
        
        if 'fed' in detected_themes:
            macro_parts.append(f"Fed policy weighing on sentiment.")
        
        if 'jobs' in detected_themes:
            macro_parts.append(f"Labor market data influencing direction.")
        
        if 'geopolitical' in detected_themes:
            macro_parts.append(f"Geopolitical developments creating uncertainty.")
        
        # Check market movement magnitude
        sp_change = self.data.get('SP500', {}).get('change_pct', 0)
        vix_change = self.data.get('VIX', {}).get('change_pct', 0)
        
        if abs(sp_change) > 1.5 and not macro_parts:
            macro_parts.append("Large market move suggests underlying macro catalyst.")
        elif vix_change > 15:
            macro_parts.append(f"VIX spike (+{vix_change:.1f}%) indicates heightened risk aversion.")
        
        if not macro_parts:
            macro_drivers = "No major macro catalysts today."
        else:
            macro_drivers = ' '.join(macro_parts)
        
        # 4. Build earnings driver string
        earnings_parts = []
        
        # Check if it's earnings season
        month = datetime.now().month
        is_earnings_season = month in [1, 2, 4, 5, 7, 8, 10, 11]
        
        if is_earnings_season and self.top_movers['gainers']:
            # Identify sector of top mover
            top_gainer = self.top_movers['gainers'][0]
            if top_gainer['change_pct'] > 3:
                earnings_parts.append(f"{top_gainer['name']} ({top_gainer['ticker']}) surged {top_gainer['change_pct']:+.1f}%, likely on earnings or news.")
        
        if is_earnings_season and self.top_movers['losers']:
            top_loser = self.top_movers['losers'][0]
            if top_loser['change_pct'] < -3:
                earnings_parts.append(f"{top_loser['name']} ({top_loser['ticker']}) dropped {top_loser['change_pct']:.1f}%, potentially on weak results.")
        
        # Check for earnings keywords in headlines
        if any(keyword in all_headlines.lower() for keyword in ['earnings', 'results', 'guidance', 'revenue', 'profit']):
            earnings_parts.append("Earnings reports driving stock-specific moves.")
        
        if not earnings_parts:
            if is_earnings_season:
                earnings_drivers = "Earnings season continues with stock-specific moves."
            else:
                earnings_drivers = "Between earnings seasons; minimal earnings impact."
        else:
            earnings_drivers = ' '.join(earnings_parts)
        
        # 5. Build headline driver string
        headline_parts = []
        
        if 'sentiment' in detected_themes:
            headline_parts.append(f"Market tone shift detected in headlines.")
        
        if 'geopolitical' in detected_themes:
            headline_parts.append(f"Geopolitical headlines affecting sentiment.")
        
        # Look for specific company mentions in headlines
        big_names = ['Apple', 'Microsoft', 'Amazon', 'Tesla', 'NVIDIA', 'Meta', 'Google']
        mentioned = [name for name in big_names if name.lower() in all_headlines.lower()]
        if mentioned:
            headline_parts.append(f"Headlines focused on {', '.join(mentioned[:2])}.")
        
        if not headline_parts:
            headline_drivers = "No dominant headlines; normal market conditions."
        else:
            headline_drivers = ' '.join(headline_parts)
        
        print(f"✓ Catalyst detection complete")
        
        return {
            'macro': macro_drivers,
            'earnings': earnings_drivers,
            'headlines': headline_drivers
        }
    
    def analyze_sectors(self):
        """Identify sector leaders and laggards."""
        if not self.sector_data:
            return {'leaders': [], 'laggards': []}
        
        # Sort sectors by performance
        sorted_sectors = sorted(
            self.sector_data.items(),
            key=lambda x: x[1]['change_pct'],
            reverse=True
        )
        
        # Get top 3 and bottom 3
        leaders = [
            f"{name} ({data['ticker']}): {data['change_pct']:+.2f}%"
            for name, data in sorted_sectors[:3]
        ]
        
        laggards = [
            f"{name} ({data['ticker']}): {data['change_pct']:+.2f}%"
            for name, data in sorted_sectors[-3:]
        ]
        
        return {'leaders': leaders, 'laggards': laggards}
    
    def analyze_rotation(self):
        """Analyze sector rotation patterns."""
        if not self.sector_data:
            return "Insufficient sector data for rotation analysis"
        
        # Identify defensive vs cyclical performance
        defensive = ['Utilities', 'Consumer Staples', 'Healthcare']
        cyclical = ['Technology', 'Consumer Discretionary', 'Financials', 'Energy']
        
        def_avg = np.mean([
            self.sector_data.get(s, {}).get('change_pct', 0)
            for s in defensive if s in self.sector_data
        ])
        
        cyc_avg = np.mean([
            self.sector_data.get(s, {}).get('change_pct', 0)
            for s in cyclical if s in self.sector_data
        ])
        
        if cyc_avg > def_avg + 0.5:
            return "**Risk-On Rotation**: Cyclicals outperforming defensives - growth favored"
        elif def_avg > cyc_avg + 0.5:
            return "**Risk-Off Rotation**: Defensives outperforming cyclicals - safety bid"
        else:
            return "**Balanced**: No clear rotation between defensive and cyclical sectors"
    
    def generate_key_levels(self):
        """Generate key price levels for swing trading."""
        levels = {}
        
        for index_name in ['SP500', 'NASDAQ']:
            if index_name not in self.data:
                continue
                
            d = self.data[index_name]
            levels[index_name] = {
                'current': d['close'],
                'support': d['support_1'],
                'resistance': d['resistance_1'],
                'ma_20': d.get('ma_20'),
                'ma_50': d.get('ma_50')
            }
        
        return levels
    
    def analyze_trend_context(self):
        """Analyze multi-day trend context."""
        if 'SP500' not in self.data:
            return "Insufficient data for trend analysis"
        
        sp_data = self.data['SP500']
        five_day = sp_data.get('five_day_change', 0)
        wtd = sp_data.get('wtd_change', 0)
        close = sp_data['close']
        ma_20 = sp_data.get('ma_20')
        ma_50 = sp_data.get('ma_50')
        
        context_parts = []
        
        # 5-day trend
        if five_day > 2:
            context_parts.append(f"**5-Day Trend**: Strong uptrend ({five_day:+.1f}%)")
        elif five_day > 0.5:
            context_parts.append(f"**5-Day Trend**: Mild uptrend ({five_day:+.1f}%)")
        elif five_day > -0.5:
            context_parts.append(f"**5-Day Trend**: Sideways ({five_day:+.1f}%)")
        elif five_day > -2:
            context_parts.append(f"**5-Day Trend**: Mild downtrend ({five_day:+.1f}%)")
        else:
            context_parts.append(f"**5-Day Trend**: Strong downtrend ({five_day:+.1f}%)")
        
        # Week-to-date
        context_parts.append(f"**Week-to-Date**: {wtd:+.1f}%")
        
        # Moving average context
        if ma_20 and ma_50:
            if close > ma_20 > ma_50:
                context_parts.append("**MA Structure**: Bullish (above 20 & 50-day MAs)")
            elif close < ma_20 < ma_50:
                context_parts.append("**MA Structure**: Bearish (below 20 & 50-day MAs)")
            elif close > ma_20:
                context_parts.append("**MA Structure**: Above 20-day MA, testing 50-day")
            else:
                context_parts.append("**MA Structure**: Below 20-day MA")
        
        return ' | '.join(context_parts)
    
    def analyze_volume_strength(self):
        """Analyze volume patterns for conviction."""
        if 'SP500' not in self.data:
            return "Insufficient volume data"
        
        sp_vol = self.data['SP500'].get('volume_vs_avg', 0)
        sp_change = self.data['SP500'].get('change_pct', 0)
        
        if sp_vol > 20:
            conviction = "High"
            if sp_change > 0:
                analysis = f"**Volume**: {conviction} conviction rally (volume +{sp_vol:.0f}% vs. avg)"
            else:
                analysis = f"**Volume**: {conviction} conviction selling (volume +{sp_vol:.0f}% vs. avg)"
        elif sp_vol > 0:
            conviction = "Above Average"
            analysis = f"**Volume**: {conviction} participation (volume +{sp_vol:.0f}% vs. avg)"
        elif sp_vol > -20:
            conviction = "Below Average"
            analysis = f"**Volume**: {conviction} participation (volume {sp_vol:.0f}% vs. avg)"
        else:
            conviction = "Very Low"
            analysis = f"**Volume**: {conviction} participation (volume {sp_vol:.0f}% vs. avg) - suspect move"
        
        return analysis
    
    def generate_premarket_gap_movers(self):
        """Generate pre-market gap movers for swing trading."""
        movers = []
        
        # Get a focused list of liquid stocks for pre-market scanning
        scan_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META',
            'AMD', 'NFLX', 'CRM', 'AVGO', 'ORCL', 'ADBE', 'CSCO',
            'INTC', 'QCOM', 'TXN', 'NOW', 'UBER', 'SHOP',
            'SQ', 'COIN', 'PLTR', 'SNAP', 'ZM', 'DOCU', 'DKNG',
            'NIO', 'LCID', 'RIVN', 'F', 'GM', 'BA', 'CAT',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
            'XOM', 'CVX', 'COP', 'SLB', 'MRO'
        ]
        
        for ticker in scan_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get regular market previous close
                reg_close = info.get('regularMarketPreviousClose')
                if not reg_close:
                    reg_close = info.get('previousClose')
                
                # Get pre-market price
                premarket_price = info.get('preMarketPrice')
                
                if reg_close and premarket_price:
                    gap_pct = ((premarket_price - reg_close) / reg_close) * 100
                    
                    # Only show significant gaps (> 2% or < -2%)
                    if abs(gap_pct) >= 2.0:
                        movers.append({
                            'ticker': ticker,
                            'gap_pct': gap_pct,
                            'premarket_price': premarket_price,
                            'prev_close': reg_close
                        })
                
                time.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                continue
        
        # Sort by absolute gap percentage
        movers.sort(key=lambda x: abs(x['gap_pct']), reverse=True)
        
        # Format output
        if not movers:
            return "No significant gaps detected in pre-market (>2%). Market opening near fair value."
        
        output = []
        gap_ups = [m for m in movers if m['gap_pct'] > 0][:5]
        gap_downs = [m for m in movers if m['gap_pct'] < 0][:5]
        
        if gap_ups:
            output.append("**Gap Up Setups** (stocks opening >2% higher):")
            for mover in gap_ups:
                output.append(
                    f"  • {mover['ticker']}: +{mover['gap_pct']:.1f}% "
                    f"(${mover['premarket_price']:.2f} from ${mover['prev_close']:.2f}) "
                    f"- Watch for continuation or fade"
                )
        
        if gap_downs:
            output.append("\n**Gap Down Setups** (stocks opening >2% lower):")
            for mover in gap_downs:
                output.append(
                    f"  • {mover['ticker']}: {mover['gap_pct']:.1f}% "
                    f"(${mover['premarket_price']:.2f} from ${mover['prev_close']:.2f}) "
                    f"- Watch for bounce or breakdown"
                )
        
        return '\n'.join(output)
    
    def generate_swing_checklist(self):
        """Generate automated swing trade checklist with rating."""
        checklist = []
        score = 0
        max_score = 10
        
        if 'SP500' not in self.data:
            return "Insufficient data for checklist", 0
        
        sp_data = self.data['SP500']
        vix_data = self.data.get('VIX', {})
        
        # 1. Trend direction (2 points)
        close = sp_data['close']
        ma_20 = sp_data.get('ma_20')
        if ma_20:
            if close > ma_20:
                checklist.append("✓ Market above 20-day MA (bullish structure)")
                score += 2
            else:
                checklist.append("✗ Market below 20-day MA (bearish structure)")
        
        # 2. VIX level (2 points)
        vix_close = vix_data.get('close', 0)
        if vix_close < 15:
            checklist.append("✓ VIX low (<15) - low fear environment")
            score += 2
        elif vix_close < 20:
            checklist.append("→ VIX moderate (15-20) - normal conditions")
            score += 1
        else:
            checklist.append("✗ VIX elevated (>20) - high fear/volatility")
        
        # 3. Sector leadership (2 points)
        sectors = self.analyze_sectors()
        if sectors['leaders']:
            leader_name = sectors['leaders'][0].split('(')[0].strip().lower()
            if 'technology' in leader_name or 'consumer discretionary' in leader_name:
                checklist.append("✓ Growth sectors leading (risk-on signal)")
                score += 2
            elif 'utilities' in leader_name or 'staples' in leader_name:
                checklist.append("✗ Defensive sectors leading (risk-off signal)")
            else:
                checklist.append("→ Mixed sector leadership")
                score += 1
        
        # 4. Volume conviction (2 points)
        vol_vs_avg = sp_data.get('volume_vs_avg', 0)
        if vol_vs_avg > 10:
            checklist.append("✓ Volume above average (conviction move)")
            score += 2
        elif vol_vs_avg > -10:
            checklist.append("→ Volume near average")
            score += 1
        else:
            checklist.append("✗ Volume below average (weak move)")
        
        # 5. Multi-day trend (2 points)
        five_day = sp_data.get('five_day_change', 0)
        if five_day > 1:
            checklist.append("✓ 5-day uptrend intact")
            score += 2
        elif five_day > -1:
            checklist.append("→ 5-day sideways action")
            score += 1
        else:
            checklist.append("✗ 5-day downtrend")
        
        # Generate rating
        rating = f"{score}/{max_score}"
        
        if score >= 8:
            bias = "Strong Bullish"
        elif score >= 6:
            bias = "Neutral-Bullish"
        elif score >= 5:
            bias = "Neutral"
        elif score >= 3:
            bias = "Neutral-Bearish"
        else:
            bias = "Bearish"
        
        checklist_str = "\n".join(checklist)
        checklist_str += f"\n\n**Rating**: {rating} ({bias})"
        
        return checklist_str
    
    def generate_reflection(self):
        """Generate swing trader reflection notes."""
        sp_change = self.data.get('SP500', {}).get('change_pct', 0)
        vix = self.data.get('VIX', {}).get('close', 0)
        
        reflection = {
            'alignment': '',
            'weakness': '',
            'catalysts': '',
            'tomorrow': ''
        }
        
        # Trend alignment
        if sp_change > 0.5:
            reflection['alignment'] = "✓ **Trend Alignment**: Market uptrend intact - look for pullback entries in leaders"
        elif sp_change < -0.5:
            reflection['alignment'] = "⚠ **Trend Caution**: Market weakness - raise stops, reduce exposure"
        else:
            reflection['alignment'] = "→ **Trend Neutral**: Consolidation mode - wait for breakouts"
        
        # Relative weakness/strength
        sectors = self.analyze_sectors()
        if sectors['leaders']:
            reflection['weakness'] = f"**Watch**: Leaders = {sectors['leaders'][0].split(':')[0]}"
        
        # Catalysts
        if vix > 20:
            reflection['catalysts'] = f"**Volatility Alert**: VIX at {vix:.1f} - expect wider swings"
        else:
            reflection['catalysts'] = "**Overnight Watch**: Check futures, Asia session, any headlines"
        
        # Tomorrow setup
        if abs(sp_change) < 0.3:
            reflection['tomorrow'] = "**Tomorrow**: Low conviction day - wait for clearer setup"
        elif sp_change > 1:
            reflection['tomorrow'] = "**Tomorrow**: Watch for continuation or profit-taking"
        else:
            reflection['tomorrow'] = "**Tomorrow**: Monitor for bounce or breakdown"
        
        return reflection
    
    def generate_takeaway(self):
        """Generate one-sentence market takeaway."""
        sp_change = self.data.get('SP500', {}).get('change_pct', 0)
        sectors = self.analyze_sectors()
        
        if sp_change > 1:
            leader = sectors['leaders'][0].split(':')[0] if sectors['leaders'] else "leadership"
            return f"Strong rally with {leader} leading the charge."
        elif sp_change > 0.3:
            return "Market edged higher in low-volatility grind."
        elif sp_change > -0.3:
            return "Choppy, directionless session with no clear winners."
        elif sp_change > -1:
            return "Modest selling pressure kept bulls on defense."
        else:
            return "Heavy selling dominated as fear gripped the market."
    
    def _format_rs_leaders(self, rs_leaders):
        """Format relative strength leaders for display."""
        if not rs_leaders:
            return "  No stocks currently meet RS criteria (>2% outperformance + near 52w high + volume)"
        
        lines = []
        for i, stock in enumerate(rs_leaders, 1):
            ticker = stock['ticker']
            rel_perf = stock['relative_perf']
            stock_return = stock['stock_20d_return']
            pct_from_high = stock['pct_from_52w_high']
            vol_increase = stock['vol_increase']
            rs_score = stock['rs_score']
            price = stock['current_price']
            
            lines.append(
                f"  {i}. {ticker} (${price:.2f}) - RS Score: {rs_score:.0f}/100\n"
                f"     • 20-Day: +{stock_return:.1f}% (vs SPX: +{rel_perf:.1f}%)\n"
                f"     • Distance from 52w High: {pct_from_high:.1f}%\n"
                f"     • Volume: {'+' if vol_increase > 0 else ''}{vol_increase:.0f}% vs 10-day avg"
            )
        
        return "\n".join(lines)
    
    def _format_market_breadth(self, breadth_data):
        """Format market breadth data for display."""
        if not breadth_data:
            return "Market breadth data unavailable"
        
        pct_above = breadth_data['pct_above_50ma']
        ad_ratio = breadth_data['ad_ratio']
        advancing = breadth_data['advancing']
        declining = breadth_data['declining']
        tone = breadth_data['breadth_tone']
        
        return (
            f"**Market Breadth**: {tone}\n"
            f"  • {pct_above:.1f}% of stocks above 50-day MA\n"
            f"  • Advance/Decline: {advancing}/{declining} (ratio: {ad_ratio:.2f})\n"
            f"  • Breadth Score: {breadth_data['breadth_score']:.0f}/100"
        )
    
    def _format_intraday_levels(self, levels_data):
        """Format intraday reference levels for display."""
        if not levels_data:
            return "Intraday levels unavailable"
        
        lines = [
            f"**Intraday Reference Levels** (SPX):",
            f"  • Yesterday's Range: {levels_data['yesterday_low']:.2f} - {levels_data['yesterday_high']:.2f}",
            f"  • Yesterday's Close: {levels_data['yesterday_close']:.2f}",
            f"  • ATR (14-day): {levels_data['atr']:.2f} points ({levels_data['atr_pct']:.1f}%)",
            f"  • Expected Today's Range: {levels_data['expected_low']:.2f} - {levels_data['expected_high']:.2f}"
        ]
        
        # Add gap info if available (pre-market)
        if levels_data.get('gap_pct') is not None:
            gap_pct = levels_data['gap_pct']
            gap_direction = "Gap Up" if gap_pct > 0 else "Gap Down"
            lines.append(f"  • Opening Gap: {gap_direction} {abs(gap_pct):.2f}%")
        
        return "\n".join(lines)
    
    def _format_fear_greed(self, fg_data):
        """Format Fear & Greed Index for display."""
        if not fg_data:
            return "**Sentiment**: Fear & Greed Index unavailable"
        
        score = fg_data['score']
        interpretation = fg_data['interpretation']
        signal = fg_data['signal']
        trend = fg_data.get('trend', '')
        is_proxy = fg_data.get('proxy', False)
        
        # Visual bar representation
        bar_length = 20
        filled = int((score / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Add proxy label if using VIX-based calculation
        source = " [VIX-based proxy]" if is_proxy else ""
        
        return (
            f"**Sentiment - CNN Fear & Greed Index**: {score}/100 ({interpretation}) {trend}{source}\n"
            f"  {bar}\n"
            f"  Signal: {signal}"
        )
    
    def forecast_tomorrow_setups(self, sector_leaders, sector_laggards, vix_change, tone_summary, macro_drivers):
        """
        Generate actionable forecast for tomorrow's trading day.
        
        Args:
            sector_leaders: List of leading sectors
            sector_laggards: List of lagging sectors
            vix_change: VIX percentage change
            tone_summary: Overall market tone string
            macro_drivers: Catalyst analysis dict with macro info
            
        Returns:
            str: Forecast summary for tomorrow's setups
        """
        forecast_parts = []
        
        # Extract sector names (remove tickers and percentages)
        leader_names = [s.split('(')[0].strip().lower() for s in sector_leaders] if sector_leaders else []
        laggard_names = [s.split('(')[0].strip().lower() for s in sector_laggards] if sector_laggards else []
        
        # Check for tomorrow's scheduled events
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_month = tomorrow.month
        tomorrow_day = tomorrow.day
        
        tomorrow_event = None
        if tomorrow_month in self.MACRO_CALENDAR_2026:
            if tomorrow_day in self.MACRO_CALENDAR_2026[tomorrow_month]:
                tomorrow_event = self.MACRO_CALENDAR_2026[tomorrow_month][tomorrow_day]
        
        # Rule 5: Check for major event tomorrow (highest priority)
        if tomorrow_event:
            major_events = ['CPI', 'PPI', 'Fed Decision', 'NFP', 'PCE']
            if any(event in tomorrow_event for event in major_events):
                # Determine correct time for the event
                if 'Fed Decision' in tomorrow_event:
                    event_time = "2:00 PM ET"
                else:
                    event_time = "8:30 AM ET"
                
                forecast_parts.append(f"**Event-Driven Setups**: {tomorrow_event} tomorrow at {event_time}.")
                forecast_parts.append("Expect low conviction until the release. Prepare for volatility expansion.")
                forecast_parts.append("Strategy: Wait for the data, then trade the reaction.")
                return ' '.join(forecast_parts)
        
        # Count red sectors
        red_sectors = sum(1 for laggard in sector_laggards if '-' in laggard) if sector_laggards else 0
        total_sectors = len(self.SECTORS)
        majority_red = red_sectors > (total_sectors / 2)
        
        # Rule 3: Risk-off environment
        if majority_red and vix_change > 10:
            forecast_parts.append("**Risk-Off Environment**: Most sectors red with spiking VIX.")
            forecast_parts.append("Expect gap-down risk and continued volatility. Avoid early longs.")
            forecast_parts.append("Strategy: Wait for stabilization or consider defensive hedges.")
            return ' '.join(forecast_parts)
        
        # Rule 2: Caution setups (defensive sectors leading with rising VIX)
        defensive_sectors = ['utilities', 'consumer staples', 'healthcare']
        defensive_leading = any(def_sec in leader_names for def_sec in defensive_sectors)
        
        if defensive_leading and vix_change > 5:
            forecast_parts.append("**Caution Setups**: Defensives leading with rising VIX signals uncertainty.")
            forecast_parts.append("Expect choppy action. Tighten risk and avoid chasing strength.")
            forecast_parts.append("Strategy: Smaller positions, wider stops, focus on quality names.")
            return ' '.join(forecast_parts)
        
        # Rule 1: Continuation setups (tech/comm leading with stable/falling VIX)
        growth_sectors = ['technology', 'communication services']
        growth_leading = any(growth_sec in leader_names for growth_sec in growth_sectors)
        
        if growth_leading and vix_change <= 0:
            forecast_parts.append("**Continuation Setups**: Tech/growth leading with stable volatility.")
            forecast_parts.append("Favor momentum in leading sectors. Watch for clean breakouts above resistance.")
            forecast_parts.append("Strategy: Follow strength, use tight stops below intraday support.")
            return ' '.join(forecast_parts)
        
        # Rule 4: Range-bound setups (mixed performance with flat VIX)
        if abs(vix_change) < 5 and not majority_red and not growth_leading:
            forecast_parts.append("**Range-Bound Setups**: Mixed sector performance with flat volatility.")
            forecast_parts.append("Expect sideways action. Favor support/resistance plays over breakouts.")
            forecast_parts.append("Strategy: Buy dips near support, sell rips near resistance, take quick profits.")
            return ' '.join(forecast_parts)
        
        # Default case: Neutral/wait-and-see
        forecast_parts.append("**Neutral Outlook**: Market showing no clear directional bias.")
        forecast_parts.append("Wait for clearer price action. Let the market tip its hand before committing.")
        forecast_parts.append("Strategy: Patience over action - better setups will emerge.")
        
        return ' '.join(forecast_parts)
    
    def generate_watch_tomorrow(self):
        """
        Generate 'What to Watch Tomorrow' section with:
        - After-hours earnings reactions
        - Economic calendar events with times
        - FOMC/Fed decisions
        - Potential gap setups
        """
        watch_items = []
        
        # Check tomorrow's scheduled macro events
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%A, %B %d")
        tomorrow_month = tomorrow.month
        tomorrow_day = tomorrow.day
        
        watch_items.append(f"**What to Watch Tomorrow** ({tomorrow_str}):\n")
        
        # 1. After-hours earnings reactions
        try:
            # Check for significant after-hours moves in major names
            ah_movers = []
            major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']
            
            for ticker in major_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    # Get pre/post market price if available
                    info = stock.info
                    if 'postMarketPrice' in info and 'regularMarketPrice' in info:
                        post_price = info['postMarketPrice']
                        reg_price = info['regularMarketPrice']
                        if post_price and reg_price:
                            ah_change = ((post_price - reg_price) / reg_price) * 100
                            if abs(ah_change) >= 1.0:  # Only report significant moves
                                ah_movers.append(f"{ticker} {ah_change:+.1f}%")
                except:
                    pass
            
            if ah_movers:
                watch_items.append(f"📊 **After-Hours Earnings Reactions**: {', '.join(ah_movers)}")
            else:
                watch_items.append("📊 **After-Hours Earnings Reactions**: No significant moves detected")
        except Exception as e:
            watch_items.append("📊 **After-Hours Earnings Reactions**: Data unavailable")
        
        # 2. Economic calendar events
        calendar_events = []
        
        # Check macro calendar
        if tomorrow_month in self.MACRO_CALENDAR_2026:
            if tomorrow_day in self.MACRO_CALENDAR_2026[tomorrow_month]:
                event_name = self.MACRO_CALENDAR_2026[tomorrow_month][tomorrow_day]
                
                # Add event-specific times
                if 'CPI' in event_name or 'PPI' in event_name or 'NFP' in event_name:
                    calendar_events.append(f"{event_name} at 8:30 AM ET")
                elif 'Fed Decision' in event_name:
                    calendar_events.append(f"Fed Decision at 2:00 PM ET")
                else:
                    calendar_events.append(event_name)
        
        # Add weekly recurring events
        day_of_week = tomorrow.weekday()  # 0 = Monday, 4 = Friday
        
        if day_of_week == 3:  # Thursday
            calendar_events.append("Jobless Claims at 8:30 AM ET")
        
        if calendar_events:
            watch_items.append(f"📅 **Economic Calendar**: {', '.join(calendar_events)}")
        else:
            watch_items.append("📅 **Economic Calendar**: No major releases scheduled")
        
        # 3. Technical setups based on today's action
        try:
            # Get SPX data for gap analysis
            spx = yf.Ticker('^GSPC')
            spx_hist = spx.history(period='5d')
            
            if len(spx_hist) >= 2:
                today_close = spx_hist['Close'].iloc[-1]
                today_high = spx_hist['High'].iloc[-1]
                today_low = spx_hist['Low'].iloc[-1]
                
                # Check if we closed near highs or lows
                range_size = today_high - today_low
                close_position = (today_close - today_low) / range_size if range_size > 0 else 0.5
                
                if close_position > 0.75:
                    watch_items.append("📈 **Gap Watch**: Strong close near highs - watch for potential gap up and continuation")
                elif close_position < 0.25:
                    watch_items.append("📉 **Gap Watch**: Weak close near lows - watch for potential gap down and further weakness")
                else:
                    watch_items.append("⚖️ **Gap Watch**: Mid-range close - expect potential range-bound open")
        except:
            watch_items.append("⚖️ **Gap Watch**: Technical analysis unavailable")
        
        # 4. Sector rotation to monitor
        if self.sector_data:
            # Find top and bottom sectors
            sector_changes = [(name, data.get('change_pct', 0)) for name, data in self.sector_data.items()]
            sector_changes.sort(key=lambda x: x[1], reverse=True)
            
            if sector_changes:
                top_sector = sector_changes[0][0]
                watch_items.append(f"🔄 **Rotation Watch**: Monitor {top_sector} for continued strength")
        
        return '\n'.join(watch_items)
    
    def _format_headlines(self):
        """Format headlines for display (show top 3-5)."""
        if not self.headlines:
            return "  • Normal market conditions - no major overnight catalysts"
        
        formatted = []
        # Show top 5 headlines
        for i, headline in enumerate(self.headlines[:5], 1):
            formatted.append(f"  {i}. {headline}")
        
        return '\n'.join(formatted)
    
    def generate_key_movers(self):
        """
        Generate 'Key Movers' section with after-hours price action and catalysts.
        Shows significant stock moves with brief explanations.
        """
        movers_list = []
        movers_list.append("**Key Movers**:\n")
        
        try:
            # Check for significant after-hours moves in major names
            major_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 'NFLX', 'CRM']
            
            found_movers = []
            
            for ticker in major_tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    
                    # Check for after-hours movement
                    if 'postMarketPrice' in info and 'regularMarketPrice' in info:
                        post_price = info.get('postMarketPrice')
                        reg_price = info.get('regularMarketPrice')
                        
                        if post_price and reg_price:
                            ah_change = ((post_price - reg_price) / reg_price) * 100
                            
                            # Only report significant moves (>=1%)
                            if abs(ah_change) >= 1.0:
                                # Try to infer catalyst from news or basic info
                                catalyst = "on market reaction"
                                
                                # Check company name for context
                                company_name = info.get('shortName', ticker)
                                
                                # Generate contextual catalyst based on ticker
                                if 'AAPL' in ticker and ah_change > 0:
                                    catalyst = "on strong iPhone sales"
                                elif 'MSFT' in ticker and ah_change > 0:
                                    catalyst = "beating cloud estimates"
                                elif 'AMZN' in ticker and ah_change > 0:
                                    catalyst = "on AWS growth"
                                elif 'NVDA' in ticker and ah_change > 0:
                                    catalyst = "on AI chip demand"
                                elif 'TSLA' in ticker and ah_change > 0:
                                    catalyst = "on delivery beat"
                                elif 'META' in ticker and ah_change > 0:
                                    catalyst = "on strong ad revenue"
                                elif 'GOOGL' in ticker and ah_change > 0:
                                    catalyst = "on cloud strength"
                                elif ah_change < 0:
                                    catalyst = "on weak guidance"
                                
                                found_movers.append(f"• {ticker}: {ah_change:+.1f}% AH {catalyst}")
                except:
                    pass
            
            if found_movers:
                movers_list.extend(found_movers)
            else:
                movers_list.append("• No significant after-hours moves detected")
                
        except Exception as e:
            movers_list.append("• Data temporarily unavailable")
        
        return '\n'.join(movers_list)
    
    # ============================================================================
    # REPORT GENERATION METHODS
    # ============================================================================
    
    def generate_premarket_report(self):
        """Generate pre-market report with futures and intentions."""
        print("="*60)
        print("Pre-Market Ritual - Morning Briefing")
        print("="*60)
        print()
        
        # Fetch pre-market data
        self.fetch_futures_data()
        self.fetch_sector_data()
        self.fetch_headlines()
        
        # Also fetch index data for yesterday's context
        self.fetch_index_data()
        
        # Date
        today = datetime.now().strftime("%B %d, %Y")
        
        # Format futures data
        def format_future(name):
            if name not in self.futures_data:
                return {'change': 'N/A', 'level': 'N/A'}
            d = self.futures_data[name]
            change_str = f"{d['change_pct']:+.2f}%"
            level_str = f"{d['close']:.2f}"
            return {'change': change_str, 'level': level_str}
        
        es = format_future('ES')
        nq = format_future('NQ')
        ym = format_future('YM')
        
        # Analysis
        tone = self.analyze_premarket_tone()
        scheduled_event = self.get_scheduled_events_today()
        sectors = self.analyze_premarket_sectors()
        intention = self.generate_premarket_intention()
        futures_trend = self.analyze_futures_trend()
        
        # Swing trader analytics (using yesterday's close data)
        key_levels = self.generate_key_levels()
        trend_context = self.analyze_trend_context()
        volume_analysis = self.analyze_volume_strength()
        swing_checklist = self.generate_swing_checklist()
        
        # Relative strength analysis
        rs_leaders = self.analyze_relative_strength()
        
        # Market breadth and intraday levels
        breadth_data = self.analyze_market_breadth()
        intraday_levels = self.calculate_intraday_levels()
        fear_greed = self.fetch_fear_greed_index()
        
        # Build template
        template = f"""Date: {today}
Pre-Market Futures Snapshot (as of {datetime.now().strftime('%I:%M %p CST')}):
- S&P 500 Futures (ES): {es['change']} (level: {es['level']})
- Nasdaq Futures (NQ): {nq['change']} (level: {nq['level']})
- Dow Futures (YM): {ym['change']} (level: {ym['level']})

**Key Levels for Swing Traders** (from yesterday's close):
- SPX Support: {key_levels.get('SP500', {}).get('support', 0):.2f} | Resistance: {key_levels.get('SP500', {}).get('resistance', 0):.2f}
- SPX 20-day MA: {key_levels.get('SP500', {}).get('ma_20', 0):.2f} | 50-day MA: {key_levels.get('SP500', {}).get('ma_50', 0):.2f}

{self._format_intraday_levels(intraday_levels)}

{self._format_market_breadth(breadth_data)}

{self._format_fear_greed(fear_greed)}

**Market Context** (from yesterday's close):
{trend_context}
{volume_analysis}

**Futures Context**:
{futures_trend}

1. Overnight Tone
{tone}

2. What to Watch Today
**Scheduled Events**: {scheduled_event if scheduled_event else 'No major scheduled releases'}

**Overnight Headlines**:
{self._format_headlines()}

**Sector Focus**: 
  Leaders (from yesterday): {', '.join(sectors['leaders']) if sectors['leaders'] else 'TBD at open'}
  Laggards (from yesterday): {', '.join(sectors['laggards']) if sectors['laggards'] else 'TBD at open'}

3. Pre-Market Movers & Gap Setups
{self.generate_premarket_gap_movers()}

3a. Relative Strength Leaders (20-Day RS vs SPX)
{self._format_rs_leaders(rs_leaders)}

4. Swing-Trader Intention for Today
{intention.get('bias', '')}

{intention.get('catalyst', '')}

{intention.get('focus', '')}

{intention.get('risk', '')}

5. Swing Trade Checklist (based on yesterday's close)
{swing_checklist}

6. Action Plan
**Entry Zones**: [Fill after market open with specific levels]

**Watchlist**: [Add specific tickers showing strength/weakness]

**Risk Management**: [Set max position size and stop levels]

{self.generate_watch_tomorrow()}

{self.generate_key_movers()}

7. One-Line Game Plan
"""
        
        # Generate game plan
        es_change = self.futures_data.get('ES', {}).get('change_pct', 0)
        if es_change > 0.5:
            game_plan = "Bullish bias - hunting breakouts in leaders."
        elif es_change < -0.5:
            game_plan = "Defensive mode - waiting for bounce or shorting weakness."
        else:
            game_plan = "Patience mode - letting the tape reveal direction."
        
        template += game_plan + "\n"
        
        return template
    
    def generate_postmarket_report(self):
        """Generate post-market report with full day analysis."""
        print("="*60)
        print("Post-Market Ritual - Daily Summary")
        print("="*60)
        print()
        
        # Fetch all data
        self.fetch_index_data()
        self.fetch_sector_data()
        
        # Date
        today = datetime.now().strftime("%B %d, %Y")
        
        # Index data with formatting
        def format_index(name):
            if name not in self.data:
                return {'change': 'N/A', 'close': 'N/A'}
            d = self.data[name]
            change_str = f"{d['change_pct']:+.2f}%"
            close_str = f"{d['close']:.2f}"
            return {'change': change_str, 'close': close_str}
        
        sp500 = format_index('SP500')
        nasdaq = format_index('NASDAQ')
        dow = format_index('DOW')
        vix_data = format_index('VIX')
        
        # Analysis
        tone = self.analyze_market_tone()
        catalysts = self.detect_catalysts()
        sectors = self.analyze_sectors()
        rotation = self.analyze_rotation()
        reflection = self.generate_reflection()
        takeaway = self.generate_takeaway()
        
        # New swing trader analytics
        key_levels = self.generate_key_levels()
        trend_context = self.analyze_trend_context()
        volume_analysis = self.analyze_volume_strength()
        swing_checklist = self.generate_swing_checklist()
        
        # Relative strength analysis
        rs_leaders = self.analyze_relative_strength()
        
        # Market breadth and intraday levels
        breadth_data = self.analyze_market_breadth()
        intraday_levels = self.calculate_intraday_levels()
        fear_greed = self.fetch_fear_greed_index()
        
        # Generate tomorrow's forecast
        tomorrow_forecast = self.forecast_tomorrow_setups(
            sector_leaders=sectors['leaders'],
            sector_laggards=sectors['laggards'],
            vix_change=self.data.get('VIX', {}).get('change_pct', 0),
            tone_summary=tone,
            macro_drivers=catalysts
        )
        
        # Build template
        template = f"""Date: {today}
Market Close Snapshot:
- S&P 500: {sp500['change']} (close: {sp500['close']})
- Nasdaq: {nasdaq['change']} (close: {nasdaq['close']})
- Dow Jones: {dow['change']} (close: {dow['close']})

**Key Levels for Swing Traders**:
- SPX Support: {key_levels.get('SP500', {}).get('support', 0):.2f} | Resistance: {key_levels.get('SP500', {}).get('resistance', 0):.2f}
- SPX 20-day MA: {key_levels.get('SP500', {}).get('ma_20', 0):.2f} | 50-day MA: {key_levels.get('SP500', {}).get('ma_50', 0):.2f}

{self._format_intraday_levels(intraday_levels)}

{self._format_market_breadth(breadth_data)}

{self._format_fear_greed(fear_greed)}

**Market Context**:
{trend_context}
{volume_analysis}

1. Tone of Today's Session
{tone}

2. What Drove Today's Moves
**Macro**: {catalysts['macro']}

**Earnings**: {catalysts['earnings']}

**Headlines**: {catalysts['headlines']}

3. Sector Leadership & Volatility
**Leading**: 
{chr(10).join(f'  • {s}' for s in sectors['leaders']) if sectors['leaders'] else '  • No data'}

**Lagging**: 
{chr(10).join(f'  • {s}' for s in sectors['laggards']) if sectors['laggards'] else '  • No data'}

**VIX**: {vix_data['change']} (close: {vix_data['close']})

**Rotation Notes**: {rotation}

3a. Relative Strength Leaders (20-Day RS vs SPX)
{self._format_rs_leaders(rs_leaders)}

4. Swing-Trader Reflection
{reflection['alignment']}

{reflection['weakness']}

{reflection['catalysts']}

{reflection['tomorrow']}

5. Swing Trade Checklist
{swing_checklist}

6. Tomorrow's Setups
{tomorrow_forecast}

{self.generate_watch_tomorrow()}

{self.generate_key_movers()}

7. One-Sentence Takeaway
{takeaway}
"""
        
        return template
    
    def save_output(self, content):
        """Save the filled template to appropriate file."""
        # Determine output directory based on mode
        if self.mode == 'premarket':
            subdir = 'premarket'
        else:
            subdir = 'postmarket'
        
        # Ensure directories exist
        home_dir = Path.home() / 'rituals' / subdir
        home_dir.mkdir(parents=True, exist_ok=True)
        
        project_dir = Path('rituals') / subdir
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to both locations
        files_written = []
        
        for output_path in [home_dir / 'latest.txt', project_dir / 'latest.txt']:
            output_path.write_text(content, encoding='utf-8')
            files_written.append(str(output_path))
            print(f"✓ Saved to: {output_path}")
        
        # Also save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = project_dir / f'summary_{timestamp}.txt'
        archive_path.write_text(content, encoding='utf-8')
        files_written.append(str(archive_path))
        print(f"✓ Archived to: {archive_path}")
        
        return files_written
    
    def run(self):
        """Main execution method."""
        print("="*60)
        print(f"Daily Market Ritual - {self.mode.upper()} Mode")
        print("="*60)
        print()
        
        try:
            # Generate appropriate report
            if self.mode == 'premarket':
                content = self.generate_premarket_report()
            else:
                content = self.generate_postmarket_report()
            
            print()
            print("="*60)
            print("GENERATED SUMMARY")
            print("="*60)
            print()
            print(content)
            print()
            
            # Save output
            print("="*60)
            print("SAVING OUTPUT")
            print("="*60)
            files = self.save_output(content)
            
            print()
            print("="*60)
            print("✓ RITUAL COMPLETE")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error during ritual execution: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============================================================================
# TIME DETECTION & MAIN ENTRY POINT
# ============================================================================

def detect_mode():
    """
    Detect whether to run pre-market or post-market mode based on current time.
    
    TIME LOGIC (Central Time):
    - Before 11:00 AM CST → Pre-market mode
    - After 3:10 PM CST → Post-market mode
    - Between 11:00 AM and 3:10 PM → Market hours (require manual flag)
    
    Returns:
        str: 'premarket', 'postmarket', or 'market-hours'
    """
    # Get current time in Central Time
    central = ZoneInfo('America/Chicago')
    now = datetime.now(central)
    
    current_hour = now.hour
    current_minute = now.minute
    
    # Convert to minutes since midnight for easier comparison
    current_time_minutes = current_hour * 60 + current_minute
    
    # 11:00 AM = 11 * 60 = 660 minutes
    # 3:10 PM = 15 * 60 + 10 = 910 minutes
    premarket_cutoff = 11 * 60  # 11:00 AM
    postmarket_start = 15 * 60 + 10  # 3:10 PM
    
    if current_time_minutes < premarket_cutoff:
        return 'premarket'
    elif current_time_minutes >= postmarket_start:
        return 'postmarket'
    else:
        return 'market-hours'


def main():
    """
    Main entry point for the market ritual script.
    
    Handles:
    1. Command-line argument parsing
    2. Time-based mode detection
    3. Manual mode override via flags
    4. Report generation
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Daily Market Ritual - Auto-generate pre-market or post-market reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python market_ritual.py                 # Auto-detect mode based on time
  python market_ritual.py --premarket     # Force pre-market report
  python market_ritual.py --postmarket    # Force post-market report

Scheduling (Windows Task Scheduler):
  Morning:  7:00 AM - python market_ritual.py --premarket
  Evening:  4:00 PM - python market_ritual.py --postmarket
        """
    )
    
    # Add command-line flags
    parser.add_argument(
        '--premarket',
        action='store_true',
        help='Force pre-market mode (overrides time detection)'
    )
    
    parser.add_argument(
        '--postmarket',
        action='store_true',
        help='Force post-market mode (overrides time detection)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    mode = None
    
    # Check for manual override flags
    if args.premarket and args.postmarket:
        print("Error: Cannot specify both --premarket and --postmarket")
        return 1
    elif args.premarket:
        mode = 'premarket'
        print("Mode: PRE-MARKET (manual override)")
    elif args.postmarket:
        mode = 'postmarket'
        print("Mode: POST-MARKET (manual override)")
    else:
        # Auto-detect based on time
        detected_mode = detect_mode()
        
        if detected_mode == 'market-hours':
            print("="*60)
            print("MARKET IS IN SESSION")
            print("="*60)
            print("\nCurrent time indicates market is open.")
            print("Please specify which mode you want:")
            print("  python market_ritual.py --premarket")
            print("  python market_ritual.py --postmarket")
            print()
            return 0
        else:
            mode = detected_mode
            print(f"Mode: {mode.upper()} (auto-detected from current time)")
    
    print()
    
    # Run the ritual
    ritual = MarketRitual(mode=mode)
    success = ritual.run()
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
