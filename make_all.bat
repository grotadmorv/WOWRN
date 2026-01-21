@echo off
echo Running WoW gear scraper...
cd src
set PYTHONPATH=%CD%
python -m wowrn_scraper.run_scrapers
cd ..
pause
