PYTHONPATH := src
PYTHON := python

.PHONY: all scrape clean

all: scrape

scrape:
	@echo "Running WoW gear scraper..."
	set PYTHONPATH=$(PYTHONPATH) && $(PYTHON) -m wowrn_scraper.run_scrapers

clean:
	@echo "Cleaning up __pycache__..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf src/wowrn_scraper/data/*
