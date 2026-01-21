import pytest
from wowrn_scraper.wowhead.main import (
    extract_item_mapping,
    extract_guide_markup,
    parse_item_link,
    parse_bis_items
)

@pytest.fixture
def sample_html_with_mapping():
    return """
    <html>
    <body>
    <script>
    WH.Gatherer.addData(3, 1, {"123": {"name_enus": "Test Item"}, "456": {"name_enus": "Another Item"}});
    </script>
    </body>
    </html>
    """

@pytest.fixture
def sample_html_with_markup():
    return """
    WH.markup.printHtml("My [b]Markup[/b] Content", "guide-body");
    """

def test_extract_item_mapping(sample_html_with_mapping):
    mapping = extract_item_mapping(sample_html_with_mapping)
    assert mapping["123"] == "Test Item"
    assert mapping["456"] == "Another Item"

def test_extract_guide_markup(sample_html_with_markup):
    markup = extract_guide_markup(sample_html_with_markup)
    assert markup == "My [b]Markup[/b] Content"

def test_parse_item_link():
    assert parse_item_link("Some text [item=12345] end") == "12345"
    assert parse_item_link("No item here") is None

def test_parse_bis_items():
    markup = """
    [tabs name=bis_items]
    [tab name="Raid"]
    [tr][td][b]Head[/b][/td][td][item=100][/td][/tr]
    [/tab]
    [/tabs]
    """
    mapping = {"100": "Raid Helm"}
    result = parse_bis_items(markup, mapping)
    
    assert "Raid" in result
    assert len(result["Raid"]) == 1
    assert result["Raid"][0]["id"] == "100"
    assert result["Raid"][0]["name"] == "Raid Helm"
    assert result["Raid"][0]["slot"] == "Head"
