import json
import os
from typing import Any, Dict, List, Union


def to_lua_value(value: Any, indent: int = 0) -> str:
    indent_str = "    " * indent
    if isinstance(value, dict):
        items: List[str] = []
        for k, v in value.items():
            key_str = f'["{k}"]'
            val_str = to_lua_value(v, indent + 1)
            items.append(f"{indent_str}    {key_str} = {val_str}")
        return "{\n" + ",\n".join(items) + "\n" + indent_str + "}"

    elif isinstance(value, list):
        items = [to_lua_value(v, indent + 1) for v in value]
        return (
            "{\n"
            + ",\n".join([f"{indent_str}    {item}" for item in items])
            + "\n"
            + indent_str
            + "}"
        )

    elif isinstance(value, str):
        safe_str = (
            value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        )
        return f'"{safe_str}"'

    elif isinstance(value, (int, float)):
        return str(value)

    elif value is None:
        return "nil"

    else:
        return f'"{str(value)}"'


def main() -> None:
    json_path = os.path.join("wowhead", "pve_data.json")
    lua_path = os.path.join("..", "..", "Interface", "Addons", "WOWRN", "Data.lua")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found. Run the scraper first.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"Loaded data for {len(data)} classes.")
        lua_content = "TierListAddonData = " + to_lua_value(data)

        os.makedirs(os.path.dirname(lua_path), exist_ok=True)

        with open(lua_path, "w", encoding="utf-8") as f:
            f.write(lua_content)

        print(f"Successfully generated {lua_path}")

    except Exception as e:
        print(f"Error generating Lua file: {e}")


if __name__ == "__main__":
    main()
