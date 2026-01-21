import os
import sys
from wowrn_scraper.application.scraper_service import ScraperService
from wowrn_scraper.config import WOW_CLASSES
from wowrn_scraper.infrastructure.json_adapter import JsonStorageAdapter
from wowrn_scraper.infrastructure.lua_adapter import LuaStorageAdapter
from wowrn_scraper.infrastructure.wowhead_scraper import WowheadScraper


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_output = os.path.join(base_dir, "data", "pve_data.json")
    lua_output = os.path.join(
        base_dir, "..", "..", "Interface", "Addons", "WOWRN", "Data.lua"
    )

    scraper = WowheadScraper(delay=1.0)

    storage_adapters = [
        JsonStorageAdapter(),
        LuaStorageAdapter(variable_name="TierListAddonData"),
    ]
    output_paths = [json_output, lua_output]

    service = ScraperService(
        scraper=scraper,
        storage_adapters=storage_adapters,
    )

    print("Starting WoW gear scraper...")
    print(f"Scraping {len(WOW_CLASSES)} classes...")

    try:
        result = service.run(class_specs=WOW_CLASSES, output_paths=output_paths)
        total_specs = sum(len(specs) for specs in result.specs.values())
        print(f"\nScraping complete. Processed {total_specs} specializations.")
        print("All scrapers finished successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
