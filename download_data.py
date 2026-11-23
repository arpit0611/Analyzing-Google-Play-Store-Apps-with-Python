"""Download historical Google Play Store app records from Kaggle. The dataset is available at https://www.kaggle.com/datasets/lava18/google-play-store-apps.
Run: python download_data.py
"""
from pathlib import Path
from urllib.request import urlretrieve

URL = 'https://raw.githubusercontent.com/atul-aiml/google-playstore-eda/main/googleplaystore.csv'
TARGET = Path(__file__).resolve().parent / "data" / "raw" / "googleplaystore.csv"


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists() and TARGET.stat().st_size > 100_000:
        print(f"Already downloaded: {TARGET} ({TARGET.stat().st_size:,} bytes)")
        return
    try:
        urlretrieve(URL, TARGET)
    except Exception as exc:
        TARGET.unlink(missing_ok=True)
        print("Could not download the real dataset:", exc)
        print("Open the original dataset link in README.md, download googleplaystore.csv,")
        print("and put the file here:", TARGET)
        raise SystemExit(1)
    if TARGET.stat().st_size < 100_000:
        TARGET.unlink(missing_ok=True)
        raise SystemExit("The downloaded file was unusually small. Please download manually.")
    print(f"Downloaded {TARGET.stat().st_size:,} bytes to {TARGET}")


if __name__ == "__main__":
    main()
