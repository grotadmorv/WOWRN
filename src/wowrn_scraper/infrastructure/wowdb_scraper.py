import json
import os
import re
import time
from typing import Dict, List, Optional

import requests

from wowrn_scraper.domain.models import Item, SlotItem, TrinketItem


class WowdbScraper:
    BASE_URL = "https://www.wowdb.com/items"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self, cache_path: Optional[str] = None, batch_size: int = 10, batch_delay: float = 1.5) -> None:
        self.batch_size = batch_size
        self.batch_delay = batch_delay
        
        if cache_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_path = os.path.join(base_dir, "wowrn_scraper/data", "wowdb_item_cache.json")
        
        self.cache_path = cache_path
        self.cache: Dict[str, Dict] = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _fetch_item_page(self, item_id: str) -> Optional[str]:
        url = f"{self.BASE_URL}/{item_id}"
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"  Failed to fetch item {item_id}: {e}")
            return None

    def _parse_drop_info(self, html: str) -> Dict[str, Optional[str]]:
        pattern = r'<dd class="item-extra">Dropped by <b>(.+?)</b> - (.+?)\.</dd>'
        match = re.search(pattern, html)

        if match:
            boss_name = match.group(1).strip()
            location_name = match.group(2).strip()
            source_type = "raid"
            if "dungeon" in location_name.lower():
                source_type = "dungeon"
            elif "mythic" in location_name.lower():
                source_type = "dungeon"

            return {
                "source_type": source_type,
                "boss_name": boss_name,
                "location_name": location_name,
            }

        return {
            "source_type": "quest, vendor or crafted",
            "boss_name": None,
            "location_name": None,
        }

    def get_item_loot_info(self, item_id: str) -> Dict[str, Optional[str]]:
        if item_id in self.cache:
            return self.cache[item_id]

        html = self._fetch_item_page(item_id)
        if not html:
            info = {
                "source_type": "quest, vendor or crafted",
                "boss_name": None,
                "location_name": None,
            }
        else:
            info = self._parse_drop_info(html)

        self.cache[item_id] = info
        return info

    def enrich_items_batch(self, items: List[Item]) -> List[Item]:
        enriched = []
        total_items = len(items)

        for batch_idx in range(0, len(items), self.batch_size):
            batch = items[batch_idx : batch_idx + self.batch_size]
            batch_num = batch_idx // self.batch_size + 1
            total_batches = (len(items) + self.batch_size - 1) // self.batch_size

            print(f"    Processing batch {batch_num}/{total_batches} ({len(batch)} items)...")

            for item in batch:
                loot_info = self.get_item_loot_info(item.id)
                if isinstance(item, SlotItem):
                    enriched_item = SlotItem(
                        id=item.id,
                        name=item.name,
                        slot=item.slot,
                        source_type=loot_info["source_type"],
                        boss_name=loot_info["boss_name"],
                        location_name=loot_info["location_name"],
                    )
                elif isinstance(item, TrinketItem):
                    enriched_item = TrinketItem(
                        id=item.id,
                        name=item.name,
                        tier=item.tier,
                        source_type=loot_info["source_type"],
                        boss_name=loot_info["boss_name"],
                        location_name=loot_info["location_name"],
                    )
                else:
                    enriched_item = Item(
                        id=item.id,
                        name=item.name,
                        source_type=loot_info["source_type"],
                        boss_name=loot_info["boss_name"],
                        location_name=loot_info["location_name"],
                    )

                enriched.append(enriched_item)

            if batch_idx + self.batch_size < len(items):
                print(f"    Waiting {self.batch_delay}s before next batch...")
                time.sleep(self.batch_delay)

        self._save_cache()
        print(f"  Enriched {total_items} items. Cache saved.")
        return enriched
