# WOWRN - World of Warcraft Addon instant gear-ranking 

> **"Is it worth being WORN?"**


[<img src="https://i.imgur.com/SStkgVc.png">](https://github.com/sahra-vadrot/WOWRN)

[<img src="https://imgur.com/bEzfouT.png">](https://github.com/sahra-vadrot/WOWRN)

**WOWRN** is a lightweight, high-performance addon for **World of Warcraft (Retail/Midnight)** that simplifies gear evaluation. No more tab-alt'ing to guides during your raid or dungeon! We provide a complete Top Tier Items Catalog for each class, regularly updated using reliable theorycrafting sources such as Wowhead, Icy Veins, and Bloodmallet.


## Key Features

### Instant BiS Indicators
Hover over any gear item to see if it's considered "Best-in-Slot" for your current class and specialization. 
- Supports multiple contexts: **Overall**, **Raid**, and **Mythic+**.
- Colored indicators for immediate visual clarity.

### Trinket Tier Lists
Trinkets can be complex. WOWRN labels them with their respective tiers (**S, A, B, C, D**) directly on the tooltip, based on top-tier theorycrafting data.

### Cartel Chips Integration
Specialized tooltips for Puzzling Cartel Chips and other unique gear mechanics, including helpful details on when they are most effective.

### In-game Catalog
Use `/wowrn` or `/rn` to open a searchable catalog of all ranked items. Browse by Class and Specialization to plan your next upgrade path.

### Minimap & Slash Commands
- **Minimap Button:** Quick access to the Catalog UI.
- **Slash Commands:** `/wowrn` to toggle UI, `/wowrn minimap` to toggle the button.

# TECH - Getting Started

## How it Works
- **Automated Scraping:** Fetches data from **Wowhead**, **Icy Veins** (WIP), and **Bloodmallet** (WIP).
- **Data-Driven:** Generates a Lua database table for instant lookup.
- **Lightweight:** No in-game calculation, just a static data lookup.

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

**Windows:**
Run the all-in-one batch script to scrape data and generate the Lua file:
```cmd
.\make_all.bat
```

**Linux/KPI:**
Use the Makefile:
```bash
make all
```

**What happens:**
1. Scrapers run (Wowhead, etc.).
2. JSON data is saved to `src/wowrn_scraper/wowhead/pve_data.json`.
3. `generate_lua.py` converts the JSON to a Lua table.
4. The final file is saved to: `Interface/Addons/WOWRN/Data.lua`.

## Install the AddOn

Copy the `Interface/Addons/WOWRN` folder to your WoW addons directory.

Features:
- Shows BiS info when hovering items (Overall/Raid/Mythic+)
- Displays trinket tier (S/A/B/C/D/F)
- Auto-detects your class and specialization

## Development

### Code Quality
We use **Black** for formatting and **isort** for import sorting.
```bash
black src tests
isort src tests
```

### Testing
Run unit tests with **pytest**:
```bash
python -m pytest
```

## License

This project is licensed under the **GNU General Public License v3.0**.
**SPDX Identifier:** `GPL-3.0-or-later`
See the `LICENSE` file for the full license text.

## Copyright
**&copy; 2026 Sahra Vadrot. All rights reserved.**
