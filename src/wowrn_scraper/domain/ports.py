from typing import Protocol

from wowrn_scraper.domain.models import ScrapingResult, SpecData


class ScraperPort(Protocol):
    def scrape_spec(self, class_name: str, spec_name: str) -> SpecData:
        ...


class StoragePort(Protocol):
    def save(self, result: ScrapingResult, output_path: str) -> None:
        ...
