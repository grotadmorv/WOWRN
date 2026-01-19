# WOWRN - World of Warcraft Addon instant gear-ranking 

> **"Is it worth being WORN?"**

**WOWRN** is a lightweight, data-driven addon for **World of Warcraft: Midnight (12.0)**. It provides instant gear-ranking clarity by injecting Tier List data from top theorycrafting sites directly into your in-game tooltips.
To eliminate the need for Alt-Tabbing. When you hover over an item in your bags, loot window, or the Great Vault, WOWRN tells you exactly where that item stands in the current meta for your specific class and specialization.

## Architecture: The Simple Sync

WOWRN uses a simple "Static Database" approach to ensure maximum performance and zero UI errors.

### 1. The Scraper (`/scraper`)
* **Source:** Scrapes **WoWhead** (Tier Lists) and **Bloodmallet** (Trinket/Ring rankings).
* **Tech:** Python.
* **Output:** Generates a single `Data.lua` file containing a table of `ItemID -> Rank`.

### 2. The Addon (`/Interface/Addons/WOWRN`)
* **Tech:** Lua.
* **Hook:** Uses the Midnight-optimized `TooltipDataProcessor`.
* **Action:** On hover, it matches the item ID with the data in `Data.lua` and adds a clean, color-coded line to the tooltip.

##  Roadmap
Phase 1: The Core (Current)
Automated daily scraping of WoWhead/Bloodmallet.

Reliable in-game tooltip display for all Midnight gear.

Phase 2: Deep Integration (Future)
WOWRN Web Portal: A website where users can register and sync their characters.

Personalized Simulations: Integration with SimulationCraft to provide "Personal Upgrades" based on your character's exact stats, rather than general tier lists.

Custom Stat Weights: Allow users to upload their own weights via the website to be "baked" into their private addon update.


## License

This project is licensed under the **GNU General Public License v3.0**.

You are free to use, modify, and redistribute this software under the terms of the GPL v3.0.  
Any distributed derivative work must also be licensed under GPL v3.0 and include source code.

**SPDX Identifier:** `GPL-3.0-or-later`

See the `LICENSE` file for the full license text.
