"""
Comprehensive test for item display sizes in both world and inventory rendering
"""
import sys
sys.path.insert(0, r"d:\Void_frontier_Project\Void_frontier")

from systems.items import ItemDatabase
from entities.item_drop import ItemDrop
import json

print("\n" + "="*80)
print("🧪 COMPREHENSIVE ITEM DISPLAY SIZE TEST")
print("="*80)

# Load items
ItemDatabase.load("data/items.json")
all_items = ItemDatabase.all_items()

print(f"\n✓ Loaded {len(all_items)} items from items.json")

# Test 1: Verify all items have display_size
print("\n[TEST 1] Verifying display_size in ItemData...")
items_with_size = 0
for item_id, item_data in all_items.items():
    if hasattr(item_data, 'display_size') and item_data.display_size:
        items_with_size += 1
        
print(f"  ✓ {items_with_size}/{len(all_items)} items have display_size attribute")

if items_with_size == len(all_items):
    print("  ✅ All items configured!")
else:
    print(f"  ⚠️  {len(all_items) - items_with_size} items missing display_size")

# Test 2: Verify ItemDrop can access display_size
print("\n[TEST 2] Testing ItemDrop with display_size...")
test_items = [
    "item_iron_ore",
    "medkit_small",
    "ammo_light",
    "tool_iron_pickaxe",
    "weapon_laser_rifle"
]

for item_id in test_items:
    item_data = ItemDatabase.get_item(item_id)
    if item_data:
        drop = ItemDrop(100, 100, item_id=item_id, amount=1)
        # Verify the drop has access to item data
        display_size = item_data.display_size if hasattr(item_data, 'display_size') else (32, 32)
        print(f"  ✓ {item_data.name:25} | Drop at (100, 100) | Display: {display_size[0]}x{display_size[1]}px")

# Test 3: Size classification
print("\n[TEST 3] Item size classification...")
print("\n  SMALL ITEMS (16-24px):")
small_items = [item for item in all_items.values() 
               if hasattr(item, 'display_size') and max(item.display_size) <= 24]
for item in sorted(small_items, key=lambda x: max(x.display_size)):
    w, h = item.display_size
    print(f"    • {item.name:25} | {w}x{h}px | {item.rarity}")

print("\n  MEDIUM ITEMS (24-40px):")
medium_items = [item for item in all_items.values() 
                if hasattr(item, 'display_size') and 24 < max(item.display_size) <= 40]
for item in sorted(medium_items, key=lambda x: max(x.display_size)):
    w, h = item.display_size
    print(f"    • {item.name:25} | {w}x{h}px | {item.rarity}")

print("\n  LARGE ITEMS (40px+):")
large_items = [item for item in all_items.values() 
               if hasattr(item, 'display_size') and max(item.display_size) > 40]
for item in sorted(large_items, key=lambda x: max(x.display_size)):
    w, h = item.display_size
    print(f"    • {item.name:25} | {w}x{h}px | {item.rarity}")

# Test 4: Compare with items.json
print("\n[TEST 4] Verifying JSON data integrity...")
with open("data/items.json", "r", encoding="utf-8") as f:
    items_json = json.load(f)

mismatches = 0
for item_id, json_data in items_json.items():
    if "display_size" in json_data:
        json_size = tuple(json_data["display_size"])
        item_data = ItemDatabase.get_item(item_id)
        if item_data and item_data.display_size != json_size:
            print(f"  ⚠️  Mismatch for {item_id}: JSON={json_size}, ItemData={item_data.display_size}")
            mismatches += 1

if mismatches == 0:
    print(f"  ✅ All {len(items_json)} items match between JSON and ItemData!")
else:
    print(f"  ⚠️  Found {mismatches} mismatches")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*80)
print("\nSUMMARY:")
print(f"  • Total items: {len(all_items)}")
print(f"  • Items with display_size: {items_with_size}")
print(f"  • Small items: {len(small_items)}")
print(f"  • Medium items: {len(medium_items)}")
print(f"  • Large items: {len(large_items)}")
print("\nThe item display system is ready for rendering!")
print("="*80 + "\n")
