@echo off
chcp 65001 > nul
echo ======================================================
echo Uruchamianie testów jednostkowych planera STRIPS...
echo ======================================================
python test_planner.py
pause
