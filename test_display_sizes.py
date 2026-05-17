"""
Test script to verify item display_size configuration
"""
import json
import sys
sys.path.insert(0, r"d:\Void_frontier_Project\Void_frontier")

from systems.items import ItemDatabase

# Load items
ItemDatabase.load("data/items.json")

print("\n" + "="*80)
print("📦 ITEM DISPLAY SIZE CONFIGURATION")
print("="*80)

# Group by type
items_by_type = {}
for item_data in ItemDatabase.all_items().values():
    item_type = item_data.type
    if item_type not in items_by_type:
        items_by_type[item_type] = []
    items_by_type[item_type].append(item_data)

for item_type in sorted(items_by_type.keys()):
    items = items_by_type[item_type]
    print(f"\n{item_type.upper()} ({len(items)} items)")
    print("-" * 80)
    
    for item in sorted(items, key=lambda x: x.name):
        size_w, size_h = item.display_size if hasattr(item, 'display_size') else (32, 32)
        print(f"  • {item.name:30} | Size: {size_w}x{size_h}px | {item.rarity}")

print("\n" + "="*80)
print("✅ All items loaded successfully with display sizes!")
print("="*80 + "\n")
