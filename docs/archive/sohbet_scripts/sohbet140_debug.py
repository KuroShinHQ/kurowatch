"""Debug FitGirl import error."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
try:
    from backend.scraper.fitgirl import FitGirlScraper
    print("FitGirl import OK")
    fs = FitGirlScraper()
    print("FitGirlScraper() OK")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
