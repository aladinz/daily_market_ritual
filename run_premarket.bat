@echo off
cd /d C:\Users\aladi\Daily_Market_Ritual

REM Activate Python environment
call .venv\Scripts\activate.bat

REM Run your ritual script
python market_ritual.py --premarket

REM Update heartbeat
echo { "last_updated": "%date% %time% CST", "mode": "premarket" } > heartbeat.json

REM Git configuration for this run
git config user.name "aladinz.github.io"
git config user.email "aladinz@gmail.com"

REM Add and commit changes
git add .
git commit -m "Automated pre-market update %date% %time%"

REM Push using PAT instead of password
git push https://github.com/aladinz/daily_market_ritual.git main

pause