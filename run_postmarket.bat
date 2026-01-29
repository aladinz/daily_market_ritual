@echo off
setlocal

REM Navigate to ritual engine folder
cd /d C:\Users\aladi\Daily_Market_Ritual

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Generate the ritual (force premarket or postmarket depending on task)
python market_ritual.py --postmarket

REM Convert to JSON for the dashboard
python convert_to_json.py

REM Commit and push to GitHub
git add .
git commit -m "Automated pre-market update %date% %time%"
git push

endlocal