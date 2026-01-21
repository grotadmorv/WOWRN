import os
import subprocess
import sys
from typing import List, Tuple

SCRAPERS: List[Tuple[str, str]] = [
    ("wowhead", "wowhead/main.py"),
    ("icyveins", "icyveins/main.py"),
    ("bloodmallet", "bloodmallet/main.py"),
]


def run_scraper(name: str, relative_path: str) -> bool:
    print(f"--- Running {name} scraper ---")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, relative_path)

    if not os.path.exists(script_path):
        print(f"Error: Script {script_path} not found.")
        return False

    try:
        script_dir = os.path.dirname(script_path)
        script_name = os.path.basename(script_path)
        src_path = os.path.dirname(base_dir)
        
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{current_pythonpath}"

        subprocess.run([sys.executable, script_name], cwd=script_dir, env=env, check=True)
        print(f"--- {name} finished successfully ---\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"--- {name} FAILED with exit code {e.returncode} ---\n")
        return False


def main() -> None:
    success = True
    for name, path in SCRAPERS:
        if not run_scraper(name, path):
            success = False

    if success:
        print("All scrapers finished successfully.")
        sys.exit(0)
    else:
        print("Some scrapers failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
