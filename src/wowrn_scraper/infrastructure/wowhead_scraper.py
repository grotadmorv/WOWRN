import json
import re
import time
from typing import Dict, List, Optional

import requests

from wowrn_scraper.domain.models import (
    BisList,
    CartelChipItem,
    SlotItem,
    SpecData,
    TrinketItem,
    TrinketTierList,
)


class WowheadScraper:
    BASE_URL = "https://www.wowhead.com/guide/classes"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self, delay: float = 1.0) -> None:
        self.delay = delay

    def scrape_spec(self, class_name: str, spec_name: str) -> SpecData:
        url = f"{self.BASE_URL}/{class_name}/{spec_name}/bis-gear"
        print(f"Scraping {spec_name} {class_name}...")

        html = self._get_html(url)
        if not html:
            return SpecData(
                class_name=class_name,
                spec_name=spec_name,
                error="Failed to fetch",
            )

        item_mapping = self._extract_item_mapping(html)
        markup = self._extract_guide_markup(html)

        if not markup:
            print("  No Guide Markup found.")
            return SpecData(
                class_name=class_name,
                spec_name=spec_name,
                url=url,
                error="No markup found",
            )

        bis_lists = self._parse_bis_items(markup, item_mapping)
        cartel_chips = self._parse_cartel_chips(markup, item_mapping)
        trinket_tier_list = self._parse_trinkets(markup, item_mapping)

        time.sleep(self.delay)

        return SpecData(
            class_name=class_name,
            spec_name=spec_name,
            url=url,
            bis_lists=bis_lists,
            cartel_chips=cartel_chips,
            trinket_tier_list=trinket_tier_list,
        )

    def _get_html(self, url: str) -> Optional[str]:
        try:
            response = requests.get(url, headers=self.HEADERS)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _extract_item_mapping(self, html: str) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        pattern = re.compile(
            r"WH\.Gatherer\.addData\(3, 1,\s*({.*?})\);", re.DOTALL
        )
        matches = pattern.findall(html)
        for json_str in matches:
            try:
                data = json.loads(json_str)
                for item_id, info in data.items():
                    if "name_enus" in info:
                        mapping[str(item_id)] = info["name_enus"]
            except json.JSONDecodeError as e:
                print(f"Error decoding item mapping JSON: {e}")
        return mapping

    def _extract_guide_markup(self, html: str) -> Optional[str]:
        pattern = re.compile(
            r'WH\.markup\.printHtml\(\s*"(.*?)"\s*,\s*"guide-body"', re.DOTALL
        )
        match = pattern.search(html)
        if match:
            raw_content = match.group(1)
            content = raw_content.replace(r"\"", '"')
            content = content.replace(r"\/", "/")
            content = content.replace(r"\r", "").replace(r"\n", "\n")
            return content
        return None

    def _parse_item_link(self, text: str) -> Optional[str]:
        match = re.search(r"\[item=(\d+)", text)
        if match:
            return match.group(1)
        return None

    def _parse_bis_items(
        self, markup: str, item_mapping: Dict[str, str]
    ) -> Dict[str, BisList]:
        bis_data: Dict[str, BisList] = {}
        bis_block_match = re.search(
            r"\[tabs[^\]]*bis_items[^\]]*\](.*?)\[/tabs\]", markup, re.DOTALL
        )

        if not bis_block_match:
            return bis_data

        block_content = bis_block_match.group(1)
        tabs = re.split(r'\[tab name="([^"]+)"', block_content)

        for i in range(1, len(tabs), 2):
            tab_name = tabs[i]
            content = tabs[i + 1]

            if tab_name in ["Overall", "Raid", "Mythic+"]:
                rows = re.findall(r"\[tr\](.*?)\[/tr\]", content, re.DOTALL)
                items: List[SlotItem] = []

                for row in rows:
                    cells = re.findall(r"\[td.*?\](.*?)\[/td\]", row, re.DOTALL)
                    if not cells:
                        continue

                    row_item_id = None
                    slot_name = "Unknown"

                    if len(cells) > 0:
                        slot_match = re.search(r"\[b\](.*?)\[/b\]", cells[0])
                        if slot_match:
                            slot_name = slot_match.group(1)
                        else:
                            slot_name = re.sub(r"\[.*?\]", "", cells[0]).strip()

                    for cell in cells:
                        iid = self._parse_item_link(cell)
                        if iid:
                            row_item_id = iid
                            break

                    if row_item_id:
                        items.append(
                            SlotItem(
                                id=row_item_id,
                                name=item_mapping.get(
                                    row_item_id, f"Item {row_item_id}"
                                ),
                                slot=slot_name,
                            )
                        )

                bis_data[tab_name] = BisList(context=tab_name, items=items)

        return bis_data

    def _parse_cartel_chips(
        self, markup: str, item_mapping: Dict[str, str]
    ) -> List[CartelChipItem]:
        chips: List[CartelChipItem] = []
        if "Puzzling Cartel Chips" not in markup:
            return chips

        parts = markup.split('toc="Puzzling Cartel Chips"]')
        if len(parts) < 2:
            return chips

        section = parts[1]
        ol_match = re.search(r"\[ol\](.*?)\[/ol\]", section, re.DOTALL)
        if ol_match:
            ol_content = ol_match.group(1)
            lis = re.findall(r"\[li\](.*?)\[/li\]", ol_content, re.DOTALL)
            for li in lis:
                iid = self._parse_item_link(li)
                if iid:
                    chips.append(
                        CartelChipItem(
                            id=iid,
                            name=item_mapping.get(iid, f"Item {iid}"),
                            details="Myth",
                        )
                    )
        return chips

    def _parse_trinkets(
        self, markup: str, item_mapping: Dict[str, str]
    ) -> TrinketTierList:
        trinkets: Dict[str, List[TrinketItem]] = {}
        match = re.search(
            r"\[tier-list=rows\](.*?)\[/tier-list\]", markup, re.DOTALL
        )
        if match:
            content = match.group(1)
            tiers = re.findall(r"\[tier\](.*?)\[/tier\]", content, re.DOTALL)
            for tier in tiers:
                rank_match = re.search(
                    r"\[tier-label.*?\](.*?)\[/tier-label\]", tier
                )
                rank = rank_match.group(1) if rank_match else "Unknown"
                cnt_match = re.search(
                    r"\[tier-content\](.*?)\[/tier-content\]", tier, re.DOTALL
                )
                items: List[TrinketItem] = []
                if cnt_match:
                    item_ids = re.findall(r"item=(\d+)", cnt_match.group(1))
                    seen_ids: set = set()
                    for iid in item_ids:
                        if iid not in seen_ids:
                            items.append(
                                TrinketItem(
                                    id=iid,
                                    name=item_mapping.get(iid, f"Item {iid}"),
                                    tier=rank,
                                )
                            )
                            seen_ids.add(iid)
                trinkets[rank] = items

        return TrinketTierList(tiers=trinkets)
