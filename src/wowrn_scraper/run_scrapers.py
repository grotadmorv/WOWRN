import os
import sys
from wowrn_scraper.application.scraper_service import ScraperService
from wowrn_scraper.config import WOW_CLASSES
from wowrn_scraper.infrastructure.json_adapter import JsonStorageAdapter
from wowrn_scraper.infrastructure.lua_adapter import LuaStorageAdapter
from wowrn_scraper.infrastructure.wowhead_scraper import WowheadScraper
from wowrn_scraper.infrastructure.wowdb_scraper import WowdbScraper
from wowrn_scraper.domain.models import SlotItem, TrinketItem


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
        print("\nEnriching items with loot location data from wowdb...")
        wowdb_scraper = WowdbScraper(batch_size=10, batch_delay=1.5)
        
        for class_name, specs in result.specs.items():
            for spec_name, spec_data in specs.items():
                if spec_data.error:
                    continue
                
                print(f"  Enriching {class_name}/{spec_name}...")
                for context, bis_list in spec_data.bis_lists.items():
                    if bis_list.items:
                        enriched_items = wowdb_scraper.enrich_items_batch(bis_list.items)
                        bis_list.items = enriched_items
                
                if spec_data.trinket_tier_list and spec_data.trinket_tier_list.tiers:
                    for tier, items in spec_data.trinket_tier_list.tiers.items():
                        if items:
                            enriched_items = wowdb_scraper.enrich_items_batch(items)
                            spec_data.trinket_tier_list.tiers[tier] = enriched_items

        print("\nSaving enriched data...")
        for adapter, path in zip(storage_adapters, output_paths):
            adapter.save(result, path)

        print("All scrapers finished successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Scraping failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
