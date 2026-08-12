import json
import os
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests

from wowrn_scraper.domain.models import (
    BisList,
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
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;"
            "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.wowhead.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(
        self,
        delay: float = 1.0,
        min_interval: float = 0.4,
        cache_path: Optional[str] = None,
    ) -> None:
        self.delay = delay
        self.min_interval = min_interval
        self._last_request = 0.0
        self._item_name_cache: Dict[str, str] = {}
        self._item_source_cache: Dict[str, Dict[str, Optional[str]]] = {}
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        if cache_path is None:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
            cache_path = os.path.join(
                base_dir, "data", "wowhead_item_cache.json"
            )
        self.cache_path = cache_path
        self._load_item_cache()

    def _load_item_cache(self) -> None:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
            self._item_name_cache = cache.get("names", {})
            self._item_source_cache = cache.get("sources", {})
        except (OSError, json.JSONDecodeError):
            pass

    def save_item_cache(self) -> None:
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "names": self._item_name_cache,
                    "sources": self._item_source_cache,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    def scrape_spec(self, class_name: str, spec_name: str) -> SpecData:
        url = f"{self.BASE_URL}/{class_name}/{spec_name}/bis-gear"
        print(f"Scraping {spec_name} {class_name}...")

        response = self._request(url, timeout=30)
        html = response.text if response else None
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
        trinket_tier_list = self._parse_trinkets(markup, item_mapping)

        self.save_item_cache()
        time.sleep(self.delay)

        return SpecData(
            class_name=class_name,
            spec_name=spec_name,
            url=url,
            bis_lists=bis_lists,
            trinket_tier_list=trinket_tier_list,
        )

    def _request(
        self, url: str, timeout: int = 15, tries: int = 4
    ) -> Optional[requests.Response]:
        """GET with throttling and backoff on Wowhead rate-limit codes."""
        for attempt in range(tries):
            wait = self.min_interval - (time.time() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            try:
                response = self.session.get(url, timeout=timeout)
                self._last_request = time.time()
                if response.status_code in (403, 429, 500, 502, 503):
                    backoff = 5 * (2 ** attempt)
                    print(
                        f"  {response.status_code} on {url}, "
                        f"retrying in {backoff}s..."
                    )
                    time.sleep(backoff)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                self._last_request = time.time()
                if attempt == tries - 1:
                    print(f"Error fetching {url}: {e}")
                    return None
                time.sleep(2 ** attempt)
        print(f"Error fetching {url}: rate limited after {tries} tries")
        return None

    def _fetch_item_xml(self, item_id: str) -> None:
        """Fetch name + source for an item in one XML call, then cache both."""
        response = self._request(f"{self.ITEM_URL}={item_id}&xml", timeout=10)
        if not response:
            return

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError:
            return

        item_el = root.find("item")
        if item_el is None:
            return

        name = (item_el.findtext("name") or "").strip()
        if name:
            self._item_name_cache[item_id] = name

        source_type = None
        boss_name = None
        location_name = None
        json_text = item_el.findtext("json")
        if json_text:
            try:
                obj = json.loads("{" + json_text + "}")
            except json.JSONDecodeError:
                obj = {}
            sourcemore = obj.get("sourcemore")
            if isinstance(sourcemore, list) and sourcemore:
                first_source = sourcemore[0]
                boss_name = first_source.get("n")
                location_name = boss_name
                source_type = (
                    "raid"
                    if ("z" in first_source or "bd" in first_source
                        or "t" in first_source)
                    else "dungeon"
                )
            source_arr = obj.get("source")
            if not source_type and source_arr:
                if 2 in source_arr or 1 in source_arr:
                    source_type = "raid"
                elif 4 in source_arr:
                    source_type = "crafting"
                elif 5 in source_arr:
                    source_type = "quest"

        self._item_source_cache[item_id] = {
            "source_type": source_type,
            "boss_name": boss_name,
            "location_name": location_name,
        }

    def _get_item_name(
        self, item_id: str, item_mapping: Dict[str, str]
    ) -> str:
        if item_id in item_mapping:
            return item_mapping[item_id]

        if item_id not in self._item_name_cache:
            self._fetch_item_xml(item_id)

        # Failures are not cached, so a rerun retries instead of freezing
        # "Item 12345" into the data forever.
        return self._item_name_cache.get(item_id, f"Item {item_id}")

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
        # Type 3 is "item"; the second argument varies per page section, so
        # match them all or half the items end up unnamed.
        pattern = re.compile(
            r"WH\.Gatherer\.addData\(\s*3\s*,\s*\d+\s*,\s*({.*?})\);", re.DOTALL
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

    def _parse_source_cell(self, cell: str) -> Dict[str, Optional[str]]:
        """Extract source info from a BiS table's Source column cell."""
        # Clean BBCode tags to get the text
        source_text = re.sub(r"\[/?\w[^\]]*\]", "", cell).strip()
        if not source_text:
            return {
                "source_type": None,
                "boss_name": None,
                "location_name": None,
            }

        # Identify source type from common keywords
        lower = source_text.lower()
        if "crafting" in lower or "profession" in lower:
            return {
                "source_type": "crafting",
                "boss_name": None,
                "location_name": source_text,
            }
        elif "vault" in lower or "great vault" in lower:
            return {
                "source_type": "vault",
                "boss_name": None,
                "location_name": source_text,
            }

        # Check for known dungeon names from the M+ pool
        dungeon_keywords = [
            "temple of sethraliss", "king's rest", "kings rest",
            "altar of fangs", "blinding vale", "voidscar arena",
            "priory", "rookery", "darkflame cleft", "cinderbrew",
            "theater of pain", "halls of atonement",
            "mists of tirna", "stonevault", "city of threads",
            "grim batol", "siege of boralus", "necrotic wake",
            "tidebound grotto",
        ]
        for kw in dungeon_keywords:
            if kw in lower:
                return {
                    "source_type": "dungeon",
                    "boss_name": None,
                    "location_name": source_text,
                }

        # Default: assume it's a raid boss/encounter name
        return {
            "source_type": "raid",
            "boss_name": source_text,
            "location_name": source_text,
        }

    def _canonicalize_tab_name(self, tab_name: str) -> str:
        """Canonicalize a BiS tab name to a standard context key."""
        lower = tab_name.lower()
        if "overall" in lower:
            return "Overall"
        elif "raid" in lower:
            return "Raid"
        elif "mythic" in lower:
            return "Mythic+"
        # For hero-talent-specific tabs (e.g. "Deathbringer BiS"),
        # use the tab name stripped of " BiS" as the context key.
        cleaned = re.sub(r"\s*BiS\s*$", "", tab_name, flags=re.IGNORECASE).strip()
        return cleaned if cleaned else tab_name

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

            canonical = self._canonicalize_tab_name(tab_name)

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

                # Parse source from the 3rd column if available
                source_info: Dict[str, Optional[str]] = {
                    "source_type": None,
                    "boss_name": None,
                    "location_name": None,
                }
                if len(cells) >= 3:
                    source_info = self._parse_source_cell(cells[2])

                if row_item_id:
                    if source_info["source_type"]:
                        self._item_source_cache[row_item_id] = source_info
                    items.append(
                        SlotItem(
                            id=row_item_id,
                            name=self._get_item_name(row_item_id, item_mapping),
                            slot=slot_name,
                            source_type=source_info["source_type"],
                            boss_name=source_info["boss_name"],
                            location_name=source_info["location_name"],
                        )
                    )

            bis_data[canonical] = BisList(context=canonical, items=items)

        return bis_data

    BADGE_SOURCE_TYPES = {
        "raid": "raid",
        "dungeon": "dungeon",
        "crafting": "crafting",
        "delves": "delves",
        "pvp": "pvp",
        "profession": "crafting",
        "vault": "vault",
    }

    def _source_from_badge(
        self, item_id: str, attrs: str
    ) -> Dict[str, Optional[str]]:
        """Read the source from the tier-list badge's display-options.

        Wowhead tags each trinket badge with `display-options=raid` (etc.),
        so no per-item request is needed here — hammering the item API is
        what gets the scraper 403'd mid-run. Boss and location are filled in
        later by the WowDB enrichment pass.
        """
        cached = self._item_source_cache.get(item_id)
        if cached and cached.get("source_type"):
            return cached

        source_type = None
        option_match = re.search(r"display-options=([a-z,\-]+)", attrs)
        if option_match:
            for option in option_match.group(1).split(","):
                source_type = self.BADGE_SOURCE_TYPES.get(option.strip())
                if source_type:
                    break

        info: Dict[str, Optional[str]] = {
            "source_type": source_type,
            "boss_name": None,
            "location_name": None,
        }
        if source_type:
            self._item_source_cache[item_id] = info
        return info

    def _parse_trinkets(
        self, markup: str, item_mapping: Dict[str, str]
    ) -> TrinketTierList:
        trinkets: Dict[str, List[TrinketItem]] = {}
        match = re.search(
            r"\[tier-list=rows[^\]]*\](.*?)\[/tier-list\]", markup, re.DOTALL
        )
        if match:
            content = match.group(1)
            tiers = re.findall(r"\[tier\](.*?)\[/tier\]", content, re.DOTALL)
            for tier in tiers:
                rank_match = re.search(
                    r"\[tier-label[^\]]*\](.*?)\[/tier-label\]",
                    tier,
                    re.DOTALL,
                )
                rank = (
                    rank_match.group(1).strip() if rank_match else "Unknown"
                )
                cnt_match = re.search(
                    r"\[tier-content\](.*?)\[/tier-content\]", tier, re.DOTALL
                )
                items: List[TrinketItem] = []
                if cnt_match:
                    badges = re.findall(
                        r"\[(?:item|icon-badge)=(\d+)([^\]]*)\]",
                        cnt_match.group(1),
                    )
                    seen_ids: set = set()
                    for iid, attrs in badges:
                        if iid not in seen_ids:
                            src_info = self._source_from_badge(iid, attrs)
                            items.append(
                                TrinketItem(
                                    id=iid,
                                    name=self._get_item_name(iid, item_mapping),
                                    tier=rank,
                                    source_type=src_info["source_type"],
                                    boss_name=src_info["boss_name"],
                                    location_name=src_info["location_name"],
                                )
                            )
                            seen_ids.add(iid)
                trinkets[rank] = items

        return TrinketTierList(tiers=trinkets)
