from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    source_type: Optional[str] = None 
    boss_name: Optional[str] = None
    location_name: Optional[str] = None


@dataclass(frozen=True)
class TrinketItem(Item):
    tier: str = "Unknown"


@dataclass(frozen=True)
class CartelChipItem(Item):
    details: str = ""


@dataclass(frozen=True)
class SlotItem(Item):
    slot: str = "Unknown"


@dataclass
class BisList:
    context: str
    items: List[SlotItem] = field(default_factory=list)


@dataclass
class TrinketTierList:
    tiers: Dict[str, List[TrinketItem]] = field(default_factory=dict)


@dataclass
class SpecData:
    class_name: str
    spec_name: str
    url: str = ""
    bis_lists: Dict[str, BisList] = field(default_factory=dict)
    cartel_chips: List[CartelChipItem] = field(default_factory=list)
    trinket_tier_list: Optional[TrinketTierList] = None
    error: Optional[str] = None


@dataclass
class ScrapingResult:
    specs: Dict[str, Dict[str, SpecData]] = field(default_factory=dict)
    def add_spec_data(self, spec_data: SpecData) -> None:
        if spec_data.class_name not in self.specs:
            self.specs[spec_data.class_name] = {}
        self.specs[spec_data.class_name][spec_data.spec_name] = spec_data

    def to_dict(self) -> Dict:
        result: Dict = {}
        for class_name, specs in self.specs.items():
            result[class_name] = {}
            for spec_name, spec_data in specs.items():
                if spec_data.error:
                    result[class_name][spec_name] = {"error": spec_data.error}
                else:
                    result[class_name][spec_name] = {
                        "url": spec_data.url,
                        "bis": {
                            ctx: [
                                {
                                    "slot": item.slot,
                                    "id": item.id,
                                    "name": item.name,
                                    "source_type": item.source_type,
                                    "boss_name": item.boss_name,
                                    "location_name": item.location_name,
                                }
                                for item in bis.items
                            ]
                            for ctx, bis in spec_data.bis_lists.items()
                        },
                        "cartel_chips": [
                            {"id": c.id, "name": c.name, "details": c.details}
                            for c in spec_data.cartel_chips
                        ],
                        "trinkets": (
                            {
                                tier: [
                                    {
                                        "id": t.id,
                                        "name": t.name,
                                        "source_type": t.source_type,
                                        "boss_name": t.boss_name,
                                        "location_name": t.location_name,
                                    }
                                    for t in items
                                ]
                                for tier, items in spec_data.trinket_tier_list.tiers.items()
                            }
                            if spec_data.trinket_tier_list
                            else {}
                        ),
                    }
        return result
