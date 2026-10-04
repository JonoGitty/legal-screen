"""Download CUAD (The Atticus Project, CC BY 4.0) into data/cuad/. About 18 MB.

  python3 eval/get_cuad.py
"""
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://raw.githubusercontent.com/The-Atticus-Project/cuad/main/"
OUT = Path(__file__).resolve().parents[1] / "data" / "cuad"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ("data.zip", "category_descriptions.csv"):
        print(f"downloading {name}")
        urllib.request.urlretrieve(BASE + name, OUT / name)
    with zipfile.ZipFile(OUT / "data.zip") as z:
        z.extractall(OUT)
    print(f"CUAD is in {OUT}")


if __name__ == "__main__":
    main()
