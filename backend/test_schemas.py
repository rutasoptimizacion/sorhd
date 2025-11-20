#!/usr/bin/env python3
"""Test script to identify which schema causes Pydantic recursion"""

import sys

# Test each schema one by one
schemas_to_test = [
    ("common.LocationSchema", "from app.schemas.common import LocationSchema"),
    ("route.RouteStatus", "from app.schemas.route import RouteStatus"),
    ("route.VisitStatus", "from app.schemas.route import VisitStatus"),
    ("route.OptimizationRequest", "from app.schemas.route import OptimizationRequest"),
    ("route.RouteBase", "from app.schemas.route import RouteBase"),
    ("route.VisitBase", "from app.schemas.route import VisitBase"),
]

for name, import_stmt in schemas_to_test:
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    try:
        exec(import_stmt)
        print(f"✅ {name} loaded successfully")
    except Exception as e:
        print(f"❌ {name} FAILED:")
        print(f"   Error: {type(e).__name__}: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

print("\n" + "="*60)
print("All schemas loaded successfully!")
print("="*60)
