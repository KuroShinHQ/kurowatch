from playwright_stealth import Stealth
import inspect
# Stealth class metodları
for name, method in inspect.getmembers(Stealth, predicate=inspect.isfunction):
    print(name)
