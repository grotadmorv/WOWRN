import json
import re
import time
from typing import Any, Dict, List, Optional

import requests
from wowrn_scraper.config import WOW_CLASSES

BASE_URL = "https://www.wowhead.com/guide/classes"
OUTPUT_FILE = "pve_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def get_html(url: str) -> Optional[str]:

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_item_mapping(html: str) -> Dict[str, str]:
    mapping = {}
    pattern = re.compile(r"WH\.Gatherer\.addData\(3, 1,\s*({.*?})\);", re.DOTALL)
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


def unescape_js_string(s: str) -> str:
    return s.encode("utf-8").decode("unicode_escape")


def extract_guide_markup(html: str) -> Optional[str]:
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


def parse_item_link(text: str) -> Optional[str]:
    match = re.search(r"\[item=(\d+)", text)
    if match:
        return match.group(1)
    return None


def parse_bis_items(
    markup: str, item_mapping: Dict[str, str]
) -> Dict[str, List[Dict[str, str]]]:
    bis_data: Dict[str, List[Dict[str, str]]] = {}
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
            items: List[Dict[str, str]] = []
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
                    iid = parse_item_link(cell)
                    if iid:
                        row_item_id = iid
                        break

                if row_item_id:
                    items.append(
                        {
                            "slot": slot_name,
                            "id": row_item_id,
                            "name": item_mapping.get(
                                row_item_id, f"Item {row_item_id}"
                            ),
                        }
                    )

            bis_data[tab_name] = items

    return bis_data


def parse_cartel_chips(
    markup: str, item_mapping: Dict[str, str]
) -> List[Dict[str, str]]:
    chips: List[Dict[str, str]] = []
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
            iid = parse_item_link(li)
            clean_text = re.sub(r"\[.*?\]", "", li).strip()
            if iid:
                chips.append(
                    {
                        "id": iid,
                        "name": item_mapping.get(iid, f"Item {iid}"),
                        "details": clean_text,
                    }
                )
    return chips


def parse_trinkets(
    markup: str, item_mapping: Dict[str, str]
) -> Dict[str, List[Dict[str, str]]]:
    trinkets: Dict[str, List[Dict[str, str]]] = {}
    match = re.search(r"\[tier-list=rows\](.*?)\[/tier-list\]", markup, re.DOTALL)
    if match:
        content = match.group(1)
        tiers = re.findall(r"\[tier\](.*?)\[/tier\]", content, re.DOTALL)
        for tier in tiers:
            rank_match = re.search(r"\[tier-label.*?\](.*?)\[/tier-label\]", tier)
            rank = rank_match.group(1) if rank_match else "Unknown"
            cnt_match = re.search(
                r"\[tier-content\](.*?)\[/tier-content\]", tier, re.DOTALL
            )
            items = []
            if cnt_match:
                item_ids = re.findall(r"item=(\d+)", cnt_match.group(1))
                for iid in item_ids:
                    items.append(
                        {
                            "id": iid,
                            "name": item_mapping.get(iid, f"Item {iid}"),
                        }
                    )
            unique_items = {i["id"]: i for i in items}.values()
            trinkets[rank] = list(unique_items)

    return trinkets


def main() -> None:
    data: Dict[str, Any] = {}
    for wow_class, specs in WOW_CLASSES.items():
        data[wow_class] = {}
        for spec in specs:
            print(f"Scraping {spec} {wow_class}...")
            url = f"{BASE_URL}/{wow_class}/{spec}/bis-gear"
            html = get_html(url)

            if html:
                mapping = extract_item_mapping(html)
                markup = extract_guide_markup(html)

                if markup:
                    spec_data = {
                        "url": url,
                        "bis": parse_bis_items(markup, mapping),
                        "cartel_chips": parse_cartel_chips(markup, mapping),
                        "trinkets": parse_trinkets(markup, mapping),
                    }
                    data[wow_class][spec] = spec_data
                else:
                    print("  No Guide Markup found.")
                    data[wow_class][spec] = {"error": "No markup found"}

                time.sleep(1)
            else:
                data[wow_class][spec] = {"error": "Failed to fetch"}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Scraping complete. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
