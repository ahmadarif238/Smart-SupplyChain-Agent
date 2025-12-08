#!/usr/bin/env python3
"""Quick import test to verify auth modules load correctly"""

import sys
print("Python version:", sys.version)
print("=" * 60)

try:
    print("1. Testing auth.security import...")
    from app.auth.security import create_access_token, authenticate_user
    print("   ✅ auth.security loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    print("2. Testing auth.dependencies import...")
    from app.auth.dependencies import get_current_user
    print("   ✅ auth.dependencies loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    print("3. Testing main.py import...")
    from main import app
    print("   ✅ main.py loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. Testing routes...")
    from app.routes import inventory, sales, orders, alerts, agent, feedback, memory
    print("   ✅ All routes loaded")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All imports successful! App is ready to start.")
