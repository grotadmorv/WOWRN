import json
import os

from wowrn_scraper.domain.models import ScrapingResult


class JsonStorageAdapter:
    def save(self, result: ScrapingResult, output_path: str) -> None:
        data_dict = result.to_dict()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=2)

        print(f"Successfully saved JSON to {output_path}")
