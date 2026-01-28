# 📊 Market Ritual Dashboard

A modern, beautiful, mobile-friendly dashboard for displaying daily market ritual reports.

## 🌟 Features

- **Auto-Detection**: Automatically selects pre-market or post-market report based on current time (CST)
- **Dark/Light Theme**: Automatic theme detection with manual toggle
- **Responsive Design**: Works beautifully on desktop, tablet, and mobile
- **Real-time Updates**: Displays live time in Central Time Zone
- **Smooth Animations**: Clean transitions and fade effects
- **Tab Navigation**: Easy switching between Today's Ritual, Pre-Market, and Post-Market

## 🚀 Deployment

This dashboard is designed to be deployed on **GitHub Pages**.

### Setup Instructions

1. **Push to GitHub**:
   ```bash
   cd dashboard
   git init
   git add .
   git commit -m "Initial dashboard commit"
   git branch -M main
   git remote add origin https://github.com/aladinz/daily_market_ritual.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository settings
   - Navigate to **Pages**
   - Select **Source**: Deploy from branch
   - Select **Branch**: main
   - Select **Folder**: /dashboard (or root if dashboard is your root)
   - Click **Save**

3. **Access Your Dashboard**:
   Your site will be live at: `https://aladinz.github.io/daily_market_ritual/`

## 📁 File Structure

```
dashboard/
├── index.html           # Main HTML file
├── css/
│   └── style.css        # All styles (light/dark theme)
├── js/
│   └── app.js           # Application logic
├── data/
│   ├── premarket.json   # Pre-market data
│   └── postmarket.json  # Post-market data
└── assets/              # Optional icons/images
```

## 🔄 Updating Data

The dashboard reads from two JSON files:
- `/data/premarket.json` - Pre-market ritual data
- `/data/postmarket.json` - Post-market ritual data

### JSON Format

Each JSON file should follow this structure:

```json
{
  "date": "January 28, 2026",
  "snapshot": {
    "SP500": {
      "close": "6978.60",
      "change": "+0.41%"
    }
  },
  "key_levels": {
    "support": "6962.01",
    "resistance": "6992.00",
    "ma_20": "6917.19",
    "ma_50": "6842.82"
  },
  "intraday_levels": {
    "yesterday_high": "6988.82",
    "yesterday_low": "6958.83"
  },
  "breadth": {
    "tone": "Neutral",
    "pct_above_50ma": "64.2%"
  },
  "sentiment": {
    "score": "56",
    "interpretation": "Greed"
  },
  "sections": {
    "tone": "Market tone description...",
    "catalysts": "What drove moves..."
  },
  "rs_leaders": [...],
  "checklist": {...}
}
```

## 🕐 Time-Based Auto-Selection

The dashboard automatically detects:
- **Before 11:00 AM CST** → Shows Pre-Market report
- **After 3:10 PM CST** → Shows Post-Market report
- **During market hours** → Prompts user to select manually

## 🎨 Customization

### Colors
Edit CSS variables in `css/style.css`:
```css
:root {
    --accent: #4A90E2;        /* Primary accent color */
    --success: #4CAF50;       /* Positive values */
    --danger: #F44336;        /* Negative values */
}
```

### Fonts
The dashboard uses Inter font. To change:
```html
<link href="https://fonts.googleapis.com/css2?family=YOUR_FONT&display=swap" rel="stylesheet">
```

## 🔧 Local Development

To test locally:

1. **Simple HTTP Server** (Python 3):
   ```bash
   cd dashboard
   python -m http.server 8000
   ```
   Then open: `http://localhost:8000`

2. **Live Server** (VS Code Extension):
   - Install "Live Server" extension
   - Right-click `index.html`
   - Select "Open with Live Server"

## 📱 Mobile Support

The dashboard is fully responsive:
- **Desktop**: Full multi-column layout
- **Tablet**: Optimized grid spacing
- **Mobile**: Single-column stack with touch-friendly buttons

## ⚡ Performance

- **No build tools required** - Pure HTML/CSS/JS
- **Minimal dependencies** - Only Google Fonts
- **Fast loading** - Optimized CSS with hardware acceleration
- **Smooth animations** - CSS transitions for 60fps performance

## 🐛 Troubleshooting

### Data not loading?
- Check that JSON files are in `/data/` folder
- Verify JSON syntax with a validator
- Check browser console for errors

### Theme not persisting?
- Ensure localStorage is enabled in browser
- Check browser privacy settings

### Time zone incorrect?
- Dashboard uses `America/Chicago` (CST)
- Modify in `app.js` if different zone needed

## 📝 License

Free to use and modify for personal/commercial projects.

## 🤝 Contributing

Feel free to submit issues or pull requests for improvements!

---

Built with ❤️ for swing traders
