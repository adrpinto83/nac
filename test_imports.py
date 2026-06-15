#!/usr/bin/env python3
import sys
print("Python version:", sys.version)
print("\n[1] Testing imports...")

try:
    print("  Importing fastapi...", end="")
    import fastapi
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")
    
try:
    print("  Importing app.config...", end="")
    from app.config import get_settings
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")

try:
    print("  Importing app.models...", end="")
    from app.models import init_db, close_db
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")

try:
    print("  Importing app.routers...", end="")
    from app.routers import auth, dashboard, users, devices, profiles, dns, stats
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")

try:
    print("  Importing app.scheduler...", end="")
    from app.scheduler import init_scheduler, stop_scheduler
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")

try:
    print("  Importing app.main...", end="")
    from app.main import app
    print(" ✅")
except Exception as e:
    print(f" ❌ {e}")
    import traceback
    traceback.print_exc()

print("\n✅ All imports successful!")
