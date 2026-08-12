from wowrn_scraper.infrastructure.wowhead_scraper import WowheadScraper


def _scraper(tmp_path):
    scraper = WowheadScraper(delay=0, cache_path=str(tmp_path / "cache.json"))
    # ponytail: no network in tests; source lookup is not what we assert here.
    scraper._fetch_item_xml = lambda item_id: None
    return scraper


def test_tier_label_on_its_own_line(tmp_path):
    """Wowhead puts the tier letter on a line of its own; it must not
    fall back to "Unknown"."""
    markup = (
        "[tier-list=rows grid]\n"
        "[tier]\n[tier-label bg=q5]S\n[/tier-label]\n"
        "[tier-content]\n[icon-badge=111 quality=4]\n[/tier-content]\n[/tier]\n"
        "[tier]\n[tier-label bg=q4]A\n[/tier-label]\n"
        "[tier-content]\n[icon-badge=222 quality=4]\n[/tier-content]\n[/tier]\n"
        "[/tier-list]"
    )
    result = _scraper(tmp_path)._parse_trinkets(
        markup, {"111": "Trinket One", "222": "Trinket Two"}
    )

    assert sorted(result.tiers) == ["A", "S"]
    assert [i.name for i in result.tiers["S"]] == ["Trinket One"]
    assert [i.name for i in result.tiers["A"]] == ["Trinket Two"]


def test_inline_tier_label_with_modifier(tmp_path):
    markup = (
        "[tier-list=rows grid]\n"
        "[tier][tier-label bg=q5]S+[/tier-label]"
        "[tier-content][icon-badge=333][/tier-content][/tier]\n"
        "[/tier-list]"
    )
    result = _scraper(tmp_path)._parse_trinkets(markup, {"333": "Big Trinket"})

    assert list(result.tiers) == ["S+"]
