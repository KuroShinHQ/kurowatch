"""Check FitGirl imports."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
try:
    from backend.scraper import fitgirl
    print("Import OK")
    print(dir(fitgirl))
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
