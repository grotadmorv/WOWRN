@echo off
echo Running all scrapers...
cd src/wowrn_scraper
python run_scrapers.py
echo Generating Lua file...
python generate_lua.py
pause
