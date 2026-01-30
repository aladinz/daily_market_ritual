@echo off
setlocal

REM ——————————————————————————————————————————————
REM  Navigate to ritual engine
REM ——————————————————————————————————————————————
cd /d C:\Users\aladi\Daily_Market_Ritual

REM ——————————————————————————————————————————————
REM  Activate environment
REM ——————————————————————————————————————————————
call .venv\Scripts\activate.bat

REM ——————————————————————————————————————————————
REM  Generate ritual (premarket or postmarket)
REM ——————————————————————————————————————————————
python market_ritual.py --premarket

REM ——————————————————————————————————————————————
REM  Update heartbeat for dashboard
REM ——————————————————————————————————————————————
echo { "last_updated": "%date% %time% CST", "mode": "premarket" } > heartbeat.json

REM ——————————————————————————————————————————————
REM  Git identity (safe, no secrets)
REM ——————————————————————————————————————————————
git config user.name "aladinz.github.io"
git config user.email "aladinzahran@msn.com"

REM ——————————————————————————————————————————————
REM  Commit and push (Credential Manager handles auth)
REM ——————————————————————————————————————————————
git add .
git commit -m "Automated pre-market update %date% %time%"
git push origin main

REM ——————————————————————————————————————————————
REM  Ritual complete
REM ——————————————————————————————————————————————
echo.
echo Ritual completed successfully. Review output above.
pause

endlocal