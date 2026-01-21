.PHONY: all wowhead icyveins bloodmallet

all:
	@echo "Running all scrapers..."
	cd src/wowrn_scraper && python run_scrapers.py && python generate_lua.py

wowhead:
	@echo "Running Wowhead scraper..."
	cd src/wowrn_scraper/wowhead && python main.py

icyveins:
	@echo "Running IcyVeins scraper..."
	cd src/wowrn_scraper/icyveins && python main.py

bloodmallet:
	@echo "Running Bloodmallet scraper..."
	cd src/wowrn_scraper/bloodmallet && python main.py
