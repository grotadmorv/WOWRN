
# WOWRN - World of Warcraft Addon instant gear-ranking 

> **"Is it worth being WORN?"**

**WOWRN** is a lightweight addon for **World of Warcraft: Midnight (12.0)**. It provides instant gear-ranking clarity by injecting Tier List data from top theorycrafting sites directly into your in-game tooltips.

## Features

- **Automated Scraping:** Fetches data from **Wowhead**, **Icy Veins** (WIP), and **Bloodmallet** (WIP).
- **Data-Driven:** Generates a Lua database table for instant lookup.
- **Lightweight:** No in-game calculation, just a static data lookup.

## Getting Started

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
