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
    ITEM_URL = "https://www.wowhead.com/item"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self, delay: float = 1.0) -> None:
        self.delay = delay
        self._item_name_cache: Dict[str, str] = {}

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

    def _fetch_item_name(self, item_id: str) -> Optional[str]:
        if item_id in self._item_name_cache:
            return self._item_name_cache[item_id]

        try:
            url = f"{self.ITEM_URL}={item_id}"
            response = requests.get(
                url, headers=self.HEADERS, allow_redirects=True, timeout=10
            )
            if response.status_code == 200:
                final_url = response.url
                if "/" in final_url.split("item=")[-1]:
                    slug = final_url.split("/")[-1].split("?")[0]
                    if slug and slug != str(item_id):
                        name = self._slug_to_name(slug)
                        self._item_name_cache[item_id] = name
                        return name
        except requests.RequestException:
            pass
        return None

    def _get_item_name(
        self, item_id: str, item_mapping: Dict[str, str]
    ) -> str:
        if item_id in item_mapping:
            return item_mapping[item_id]

        if item_id in self._item_name_cache:
            return self._item_name_cache[item_id]

        name = self._fetch_item_name(item_id)
        if name:
            return name

        return f"Item {item_id}"

    def _extract_item_mapping_from_anchors(self, html: str) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        anchor_pattern = re.compile(
            r'href="[^"]*?/item=(\d+)/([a-z0-9-]+)', re.IGNORECASE
        )
        bbcode_pattern = re.compile(
            r'\[url=item=(\d+)/([a-z0-9-]+)', re.IGNORECASE
        )
        for pattern in [anchor_pattern, bbcode_pattern]:
            for match in pattern.finditer(html):
                item_id = match.group(1)
                slug = match.group(2)

                if item_id not in mapping:
                    name = self._slug_to_name(slug)
                    mapping[item_id] = name

        return mapping

    def _extract_item_mapping(self, html: str) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        anchor_mapping = self._extract_item_mapping_from_anchors(html)
        mapping.update(anchor_mapping)
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

    def _slug_to_name(self, slug: str) -> str:
        words = slug.replace("-", " ").split()
        small_words = {"of", "the", "a", "an", "and", "or", "for", "in", "on", "at", "to"}

        result = []
        for i, word in enumerate(words):
            if i == 0 or i == len(words) - 1 or word.lower() not in small_words:
                result.append(word.capitalize())
            else:
                result.append(word.lower())

        return " ".join(result)

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
                                name=self._get_item_name(row_item_id, item_mapping),
                                slot=slot_name,
                            )
                        )

                bis_data[tab_name] = BisList(context=tab_name, items=items)

        return bis_data

    def _parse_cartel_chips(
        self, markup: str, item_mapping: Dict[str, str]
    ) -> List[CartelChipItem]:
        chips: List[CartelChipItem] = []
        seen_ids: set = set()
        if "Puzzling Cartel Chips" not in markup and "Cartel Chip" not in markup:
            return chips

        section = None
        section_patterns = [
            (r'toc="Puzzling Cartel Chips"\](.*?)(?:\[h2|\[h1|$)', re.DOTALL),
            (r'Puzzling Cartel Chips\[/h2\](.*?)(?:\[h2|\[h1|$)', re.DOTALL),
            (r'Cartel Chip[s]?\b(.*?)(?:\[h2|\[h1|$)', re.DOTALL | re.IGNORECASE),
        ]

        for pattern, flags in section_patterns:
            match = re.search(pattern, markup, flags)
            if match:
                section = match.group(1)
                break

        if not section:
            parts = markup.split('toc="Puzzling Cartel Chips"]')
            if len(parts) >= 2:
                section = parts[1]

        if not section:
            return chips

        for list_pattern in [r"\[ol\](.*?)\[/ol\]", r"\[ul\](.*?)\[/ul\]"]:
            list_match = re.search(list_pattern, section, re.DOTALL)
            if list_match:
                list_content = list_match.group(1)
                lis = re.findall(r"\[li\](.*?)\[/li\]", list_content, re.DOTALL)
                for li in lis:
                    iid = self._parse_item_link(li)
                    if iid and iid not in seen_ids:
                        chips.append(
                            CartelChipItem(
                                id=iid,
                                name=self._get_item_name(iid, item_mapping),
                                details="Myth",
                            )
                        )
                        seen_ids.add(iid)

        if not chips:
            item_ids = re.findall(r"\[item=(\d+)", section)
            for iid in item_ids:
                if iid not in seen_ids:
                    chips.append(
                        CartelChipItem(
                            id=iid,
                            name=self._get_item_name(iid, item_mapping),
                            details="Myth",
                        )
                    )
                    seen_ids.add(iid)
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
                                    name=self._get_item_name(iid, item_mapping),
                                    tier=rank,
                                )
                            )
                            seen_ids.add(iid)
                trinkets[rank] = items

        return TrinketTierList(tiers=trinkets)
