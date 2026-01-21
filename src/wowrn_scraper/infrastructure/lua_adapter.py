from typing import Any, List
from wowrn_scraper.domain.models import ScrapingResult


class LuaStorageAdapter:
    def __init__(self, variable_name: str = "TierListAddonData") -> None:
        self.variable_name = variable_name

    def save(self, result: ScrapingResult, output_path: str) -> None:
        import os

        data_dict = result.to_dict()
        lua_content = f"{self.variable_name} = {self._to_lua_value(data_dict)}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(lua_content)

        print(f"Successfully generated {output_path}")

    def _to_lua_value(self, value: Any, indent: int = 0) -> str:
        indent_str = "    " * indent

        if isinstance(value, dict):
            items: List[str] = []
            for k, v in value.items():
                key_str = f'["{k}"]'
                val_str = self._to_lua_value(v, indent + 1)
                items.append(f"{indent_str}    {key_str} = {val_str}")
            return "{\n" + ",\n".join(items) + "\n" + indent_str + "}"

        elif isinstance(value, list):
            items = [self._to_lua_value(v, indent + 1) for v in value]
            return (
                "{\n"
                + ",\n".join([f"{indent_str}    {item}" for item in items])
                + "\n"
                + indent_str
                + "}"
            )

        elif isinstance(value, str):
            safe_str = (
                value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )
            return f'"{safe_str}"'

        elif isinstance(value, (int, float)):
            return str(value)

        elif value is None:
            return "nil"

        else:
            return f'"{str(value)}"'
