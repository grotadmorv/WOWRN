from typing import Dict, List

from wowrn_scraper.domain.models import ScrapingResult
from wowrn_scraper.domain.ports import ScraperPort, StoragePort


class ScraperService:
    def __init__(
        self,
        scraper: ScraperPort,
        storage_adapters: List[StoragePort],
    ) -> None:
        self.scraper = scraper
        self.storage_adapters = storage_adapters

    def run(
        self,
        class_specs: Dict[str, List[str]],
        output_paths: List[str],
    ) -> ScrapingResult:
        result = ScrapingResult()

        for class_name, specs in class_specs.items():
            for spec_name in specs:
                spec_data = self.scraper.scrape_spec(class_name, spec_name)
                result.add_spec_data(spec_data)

        for adapter, path in zip(self.storage_adapters, output_paths):
            adapter.save(result, path)

        return result
