"""
Render build only: if env DOGDB_CSV_URL is set, download that URL to ./DogDB.csv
before import_dogdb_csv runs. Avoids large multipart uploads (502) to the web app.

Example URL: https://raw.githubusercontent.com/USER/REPO/main/DogDB.csv
"""
import os
import sys
import urllib.error
import urllib.request

URL = os.environ.get("DOGDB_CSV_URL", "").strip()
OUT = "DogDB.csv"
TIMEOUT = 120


def main():
    if not URL:
        print("DOGDB_CSV_URL unset — using DogDB.csv from the repository.")
        return 0
    print(f"Fetching {OUT} from DOGDB_CSV_URL …")
    req = urllib.request.Request(
        URL,
        headers={"User-Agent": "NeoProject-fetch_dogdb_build/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        print(f"ERROR: could not download CSV: {exc}", file=sys.stderr)
        return 1
    path = os.path.join(os.path.dirname(__file__), "..", OUT)
    path = os.path.normpath(path)
    with open(path, "wb") as f:
        f.write(data)
    print(f"Wrote {len(data)} bytes to {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
