try:
    import playwright_stealth
    print("playwright_stealth OK:", dir(playwright_stealth))
except ImportError as e:
    print("playwright_stealth FAIL:", e)

try:
    from playwright_stealth import stealth_async
    print("stealth_async OK")
except Exception as e:
    print("stealth_async FAIL:", e)

try:
    from playwright_stealth import Stealth
    print("Stealth class OK")
except Exception as e:
    print("Stealth class FAIL:", e)
