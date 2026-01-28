# 🚀 Dashboard Deployment Guide

Complete guide to deploy your Market Ritual Dashboard to GitHub Pages.

## 📋 Pre-Deployment Checklist

- [x] Dashboard files created
- [x] JSON converter script ready
- [x] Sample data generated
- [ ] GitHub repository configured
- [ ] GitHub Pages enabled

## 🔧 Step 1: Initialize Git Repository

```powershell
# Navigate to dashboard folder
cd C:\Users\aladi\Daily_Market_Ritual\dashboard

# Initialize Git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Market Ritual Dashboard"
```

## 🌐 Step 2: Connect to GitHub

```powershell
# Add remote repository
git remote add origin https://github.com/aladinz/daily_market_ritual.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

## ⚙️ Step 3: Configure GitHub Pages

1. Go to: https://github.com/aladinz/daily_market_ritual/settings/pages

2. Under **Source**:
   - Select: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)** or **/dashboard** (depending on your structure)
   - Click **Save**

3. Wait 2-3 minutes for deployment

4. Your dashboard will be live at:
   ```
   https://aladinz.github.io/daily_market_ritual/
   ```

## 🔄 Step 4: Automate Daily Updates

### Option A: Manual Update (Recommended to start)

```powershell
# Run your market ritual
python market_ritual.py --postmarket

# Convert to JSON
python convert_to_json.py

# Push to GitHub
cd dashboard
git add data/*.json
git commit -m "Update market data - $(Get-Date -Format 'yyyy-MM-dd')"
git push
```

### Option B: Automated Script

Create `update_dashboard.ps1`:

```powershell
#!/usr/bin/env pwsh
# Automated Dashboard Update Script

# Run market ritual
Write-Host "Running market ritual..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe market_ritual.py --postmarket

# Convert to JSON
Write-Host "Converting to JSON..." -ForegroundColor Cyan
python convert_to_json.py

# Git operations
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
cd dashboard
git add data/*.json
$date = Get-Date -Format "yyyy-MM-dd HH:mm"
git commit -m "Auto-update: Market data $date"
git push

Write-Host "✓ Dashboard updated successfully!" -ForegroundColor Green
```

Run it:
```powershell
.\update_dashboard.ps1
```

### Option C: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 4:30 PM
4. Action: Start a program
   - Program: `powershell.exe`
   - Arguments: `-File "C:\Users\aladi\Daily_Market_Ritual\update_dashboard.ps1"`
5. Finish

## 📱 Step 5: Verify Deployment

1. Visit your dashboard URL
2. Check that data loads correctly
3. Test theme toggle
4. Test tab switching
5. Verify on mobile device

## 🐛 Troubleshooting

### Dashboard shows "Unable to Load Data"
- Check that JSON files exist in `/data/` folder
- Verify JSON syntax (use https://jsonlint.com/)
- Check browser console for errors
- Ensure file paths are correct in GitHub

### 404 errors on GitHub Pages
- Verify repository is public
- Check GitHub Pages settings
- Ensure files are in correct folder
- Clear browser cache

### Data not updating
- Confirm git push succeeded
- Check GitHub Actions (if enabled)
- Verify JSON files are in repository
- Wait a few minutes for GitHub Pages to rebuild

## 🔒 Alternative: Private Dashboard

If you want to keep your dashboard private:

1. Use **GitHub Actions** to deploy to a private hosting service
2. Use **Netlify** or **Vercel** (connect your repo)
3. Use **AWS S3** + CloudFront
4. Self-host on a local server

### Netlify Deployment (Recommended for private)

1. Sign up at netlify.com
2. Connect GitHub repository
3. Build settings: None (static site)
4. Publish directory: `dashboard`
5. Deploy!

## 📊 Monitoring & Analytics

Optional: Add Google Analytics

1. Get tracking ID from analytics.google.com
2. Add to `index.html` before `</head>`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=YOUR-ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'YOUR-ID');
</script>
```

## 🎨 Customization Tips

### Change Color Theme
Edit `css/style.css`:
```css
:root {
    --accent: #YOUR-COLOR;
}
```

### Add Custom Logo
1. Add image to `/assets/logo.png`
2. Update header in `index.html`:
```html
<div class="logo">
    <img src="./assets/logo.png" alt="Logo">
    <h1>Market Ritual</h1>
</div>
```

### Modify Auto-Detection Times
Edit `js/app.js`:
```javascript
// Change pre-market time (default: 11:00 AM)
if (totalMinutes < 660) { // 660 = 11:00 AM

// Change post-market time (default: 3:10 PM)
else if (totalMinutes >= 910) { // 910 = 3:10 PM
```

## 🚀 Next Steps

1. ✅ Test locally: `python -m http.server 8000`
2. ✅ Push to GitHub
3. ✅ Enable GitHub Pages
4. ✅ Verify live dashboard
5. ✅ Set up automation
6. ✅ Share your dashboard URL!

## 📞 Need Help?

- GitHub Pages Docs: https://docs.github.com/en/pages
- GitHub Issues: Create issue in your repository
- Community: Stack Overflow with tag `github-pages`

---

**Your Dashboard URL (once deployed):**
```
https://aladinz.github.io/daily_market_ritual/
```

Happy trading! 📊🚀
