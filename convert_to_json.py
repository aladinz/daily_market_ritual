#!/usr/bin/env python3
"""
Convert Market Ritual text reports to JSON format for dashboard
Automatically parses ritual reports and generates JSON files
"""

import json
import re
from pathlib import Path
from datetime import datetime


def parse_ritual_report(report_text, report_type):
    """Parse text ritual report into structured JSON."""
    
    data = {
        "date": extract_date(report_text),
        "snapshot": {},
        "key_levels": {},
        "intraday_levels": {},
        "breadth": {},
        "sentiment": {},
        "market_context": {},
        "sections": {},
        "rs_leaders": [],
        "checklist": {}
    }
    
    # Extract snapshot (futures or market close)
    if report_type == 'premarket':
        data["snapshot"] = extract_futures_snapshot(report_text)
    else:
        data["snapshot"] = extract_market_snapshot(report_text)
    
    # Extract key levels
    data["key_levels"] = extract_key_levels(report_text)
    
    # Extract intraday levels
    data["intraday_levels"] = extract_intraday_levels(report_text)
    
    # Extract breadth
    data["breadth"] = extract_breadth(report_text)
    
    # Extract sentiment
    data["sentiment"] = extract_sentiment(report_text)
    
    # Extract market context
    data["market_context"] = extract_market_context(report_text)
    
    # Extract sections
    data["sections"] = extract_sections(report_text, report_type)
    
    # Extract RS leaders
    data["rs_leaders"] = extract_rs_leaders(report_text)
    
    # Extract checklist
    data["checklist"] = extract_checklist(report_text)
    
    return data


def extract_date(text):
    """Extract date from report."""
    match = re.search(r'Date:\s*([^\n]+)', text)
    return match.group(1).strip() if match else datetime.now().strftime("%B %d, %Y")


def extract_futures_snapshot(text):
    """Extract futures data for pre-market."""
    snapshot = {}
    
    patterns = [
        (r'S&P 500 Futures \(ES\):\s*([\+\-][\d\.]+%)\s*\(level:\s*([\d,\.]+)\)', 'ES'),
        (r'Nasdaq Futures \(NQ\):\s*([\+\-][\d\.]+%)\s*\(level:\s*([\d,\.]+)\)', 'NQ'),
        (r'Dow Futures \(YM\):\s*([\+\-][\d\.]+%)\s*\(level:\s*([\d,\.]+)\)', 'YM')
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, text)
        if match:
            snapshot[key] = {
                "change": match.group(1),
                "close": match.group(2).replace(',', '')
            }
    
    return snapshot


def extract_market_snapshot(text):
    """Extract market close data for post-market."""
    snapshot = {}
    
    patterns = [
        (r'S&P 500:\s*([\+\-][\d\.]+%)\s*\(close:\s*([\d,\.]+)\)', 'SP500'),
        (r'Nasdaq:\s*([\+\-][\d\.]+%)\s*\(close:\s*([\d,\.]+)\)', 'NASDAQ'),
        (r'Dow Jones:\s*([\+\-][\d\.]+%)\s*\(close:\s*([\d,\.]+)\)', 'DOW'),
        (r'VIX:\s*([\+\-][\d\.]+%)\s*\(close:\s*([\d,\.]+)\)', 'VIX')
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, text)
        if match:
            snapshot[key] = {
                "change": match.group(1),
                "close": match.group(2).replace(',', '')
            }
    
    return snapshot


def extract_key_levels(text):
    """Extract key price levels."""
    levels = {}
    
    patterns = [
        (r'SPX Support:\s*([\d,\.]+)', 'support'),
        (r'Resistance:\s*([\d,\.]+)', 'resistance'),
        (r'20-day MA:\s*([\d,\.]+)', 'ma_20'),
        (r'50-day MA:\s*([\d,\.]+)', 'ma_50')
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, text)
        if match:
            levels[key] = match.group(1).replace(',', '')
    
    return levels


def extract_intraday_levels(text):
    """Extract intraday reference levels."""
    levels = {}
    
    # Extract yesterday's range
    match = re.search(r"Yesterday's Range:\s*([\d,\.]+)\s*-\s*([\d,\.]+)", text)
    if match:
        levels["yesterday_low"] = match.group(1).replace(',', '')
        levels["yesterday_high"] = match.group(2).replace(',', '')
    
    # Extract yesterday's close
    match = re.search(r"Yesterday's Close:\s*([\d,\.]+)", text)
    if match:
        levels["yesterday_close"] = match.group(1).replace(',', '')
    
    # Extract ATR
    match = re.search(r'ATR \(14-day\):\s*([\d,\.]+)\s*points\s*\(([\d\.]+%)\)', text)
    if match:
        levels["atr"] = match.group(1).replace(',', '')
        levels["atr_pct"] = match.group(2)
    
    # Extract expected range
    match = re.search(r"Expected Today's Range:\s*([\d,\.]+)\s*-\s*([\d,\.]+)", text)
    if match:
        levels["expected_low"] = match.group(1).replace(',', '')
        levels["expected_high"] = match.group(2).replace(',', '')
    
    # Extract gap if present
    match = re.search(r'Opening Gap:\s*(Gap (?:Up|Down))\s*([\d\.]+%)', text)
    if match:
        levels["gap_direction"] = match.group(1)
        levels["gap_pct"] = match.group(2)
    
    return levels


def extract_breadth(text):
    """Extract market breadth data."""
    breadth = {}
    
    # Extract breadth tone
    match = re.search(r'\*\*Market Breadth\*\*:\s*([^\n]+)', text)
    if match:
        breadth["tone"] = match.group(1).strip()
    
    # Extract percentage above 50-MA
    match = re.search(r'([\d\.]+)%\s+of stocks above 50-day MA', text)
    if match:
        breadth["pct_above_50ma"] = match.group(1) + "%"
    
    # Extract A/D ratio
    match = re.search(r'Advance/Decline:\s*(\d+)/(\d+)\s*\(ratio:\s*([\d\.]+)\)', text)
    if match:
        breadth["advancing"] = match.group(1)
        breadth["declining"] = match.group(2)
        breadth["ad_ratio"] = match.group(3)
    
    # Extract breadth score
    match = re.search(r'Breadth Score:\s*(\d+)/100', text)
    if match:
        breadth["breadth_score"] = match.group(1)
    
    return breadth


def extract_sentiment(text):
    """Extract sentiment indicator data."""
    sentiment = {}
    
    # Extract score and interpretation
    match = re.search(r'CNN Fear & Greed Index\*\*:\s*(\d+)/100\s*\(([^\)]+)\)\s*([^\n]*)', text)
    if match:
        sentiment["score"] = match.group(1)
        sentiment["interpretation"] = match.group(2)
        sentiment["trend"] = match.group(3).strip()
    
    # Check if proxy
    if 'VIX-based proxy' in text:
        sentiment["proxy"] = True
    
    # Extract signal
    match = re.search(r'Signal:\s*([^\n]+)', text)
    if match:
        sentiment["signal"] = match.group(1).strip()
    
    return sentiment


def extract_market_context(text):
    """Extract market context data."""
    context = {}
    
    patterns = [
        (r'\*\*5-Day Trend\*\*:\s*([^\|]+)', 'five_day_trend'),
        (r'\*\*Week-to-Date\*\*:\s*([^\|]+)', 'wtd'),
        (r'\*\*MA Structure\*\*:\s*([^\n]+)', 'ma_structure'),
        (r'\*\*Volume\*\*:\s*([^\n]+)', 'volume')
    ]
    
    for pattern, key in patterns:
        match = re.search(pattern, text)
        if match:
            context[key] = match.group(1).strip()
    
    return context


def extract_sections(text, report_type):
    """Extract main report sections."""
    sections = {}
    
    if report_type == 'premarket':
        section_patterns = [
            (r'1\. Overnight Tone\n(.+?)(?=\n2\.|\nZ)', 'overnight_tone'),
            (r'2\. What to Watch Today\n(.+?)(?=\n3\.|\nZ)', 'what_to_watch'),
            (r'3\. Pre-Market Movers\n(.+?)(?=\n3a\.|\nZ)', 'movers'),
            (r'4\. Swing-Trader Intention for Today\n(.+?)(?=\n5\.|\nZ)', 'intention'),
            (r'6\. Action Plan\n(.+?)(?=\n7\.|\nZ)', 'action_plan'),
            (r'7\. One-Line Game Plan\n(.+?)$', 'game_plan')
        ]
    else:
        section_patterns = [
            (r'1\. Tone of Today\'s Session\n(.+?)(?=\n2\.|\nZ)', 'tone'),
            (r'2\. What Drove Today\'s Moves\n(.+?)(?=\n3\.|\nZ)', 'catalysts'),
            (r'3\. Sector Leadership & Volatility\n(.+?)(?=\n3a\.|\nZ)', 'sectors'),
            (r'4\. Swing-Trader Reflection\n(.+?)(?=\n5\.|\nZ)', 'reflection'),
            (r'6\. Tomorrow\'s Setups\n(.+?)(?=\n7\.|\nZ)', 'tomorrow_setups'),
            (r'7\. One-Sentence Takeaway\n(.+?)$', 'takeaway')
        ]
    
    for pattern, key in section_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    
    return sections


def extract_rs_leaders(text):
    """Extract relative strength leaders."""
    leaders = []
    
    # Find RS leaders section
    rs_section = re.search(r'3a\. Relative Strength Leaders.*?\n(.+?)(?=\n4\.|\nZ)', text, re.DOTALL)
    if not rs_section:
        return leaders
    
    rs_text = rs_section.group(1)
    
    # Extract each leader
    pattern = r'(\d+)\.\s+(\w+)\s+\(\$([\d\.]+)\)\s+-\s+RS Score:\s+(\d+)/100.*?20-Day:\s+\+([\d\.]+)%\s+\(vs SPX:\s+\+([\d\.]+)%\).*?Distance from 52w High:\s+([\-\d\.]+)%.*?Volume:\s+([\+\-\d]+)%'
    
    matches = re.finditer(pattern, rs_text, re.DOTALL)
    for match in matches:
        leaders.append({
            "ticker": match.group(2),
            "price": match.group(3),
            "rs_score": match.group(4),
            "stock_return": match.group(5),
            "relative_perf": match.group(6),
            "pct_from_high": match.group(7),
            "vol_increase": match.group(8).replace('+', '')
        })
    
    return leaders


def extract_checklist(text):
    """Extract swing trade checklist."""
    checklist = {}
    
    # Extract rating
    match = re.search(r'\*\*Rating\*\*:\s*([\d]+/10)\s*\(([^\)]+)\)', text)
    if match:
        checklist["rating"] = match.group(1)
        checklist["interpretation"] = match.group(2)
    
    # Extract items
    items = []
    checklist_section = re.search(r'5\. Swing Trade Checklist.*?\n(.+?)(?=\n6\.|\nZ)', text, re.DOTALL)
    if checklist_section:
        lines = checklist_section.group(1).split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('✓') or line.startswith('→') or line.startswith('✗')):
                items.append(line)
    
    checklist["items"] = items
    
    return checklist


def convert_ritual_to_json(ritual_path, output_path, report_type):
    """Convert a ritual text file to JSON."""
    try:
        # Read ritual report
        with open(ritual_path, 'r', encoding='utf-8') as f:
            report_text = f.read()
        
        # Parse to structured data
        data = parse_ritual_report(report_text, report_type)
        
        # Write JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Converted {ritual_path} → {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error converting {ritual_path}: {e}")
        return False


def main():
    """Main conversion function."""
    print("="*60)
    print("Market Ritual → JSON Converter")
    print("="*60)
    print()
    
    # Paths
    premarket_txt = Path('rituals/premarket/latest.txt')
    postmarket_txt = Path('rituals/postmarket/latest.txt')
    
    dashboard_data = Path('dashboard/data')
    dashboard_data.mkdir(parents=True, exist_ok=True)
    
    premarket_json = dashboard_data / 'premarket.json'
    postmarket_json = dashboard_data / 'postmarket.json'
    
    # Convert pre-market
    if premarket_txt.exists():
        convert_ritual_to_json(premarket_txt, premarket_json, 'premarket')
    else:
        print(f"⚠ Pre-market file not found: {premarket_txt}")
    
    # Convert post-market
    if postmarket_txt.exists():
        convert_ritual_to_json(postmarket_txt, postmarket_json, 'postmarket')
    else:
        print(f"⚠ Post-market file not found: {postmarket_txt}")
    
    print()
    print("="*60)
    print("✓ Conversion Complete")
    print("="*60)
    print()
    print("Dashboard data updated!")
    print(f"  → {premarket_json}")
    print(f"  → {postmarket_json}")
    print()
    print("Next steps:")
    print("  1. cd dashboard")
    print("  2. python -m http.server 8000")
    print("  3. Open http://localhost:8000")


if __name__ == '__main__':
    main()
