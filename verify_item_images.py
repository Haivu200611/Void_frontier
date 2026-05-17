import os
import json
from pathlib import Path
from collections import defaultdict

WORKSPACE_ROOT = r"d:\Void_frontier_Project\Void_frontier"
ITEMS_JSON = os.path.join(WORKSPACE_ROOT, "data", "items.json")
ITEMS_IMG_DIR = os.path.join(WORKSPACE_ROOT, "assets", "images", "items")

# Load items.json
with open(ITEMS_JSON, 'r', encoding='utf-8') as f:
    items_data = json.load(f)

# Collect all items by category
items_by_category = defaultdict(list)
name_to_item = {}

for item_id, item_info in items_data.items():
    item_type = item_info.get('type', 'unknown')
    display_name = item_info.get('name', '')
    name_to_item[display_name] = (item_id, item_type)
    items_by_category[item_type].append((item_id, display_name))

# Collect all images
images_by_category = defaultdict(list)
all_images = {}

for root, dirs, files in os.walk(ITEMS_IMG_DIR):
    for filename in files:
        if filename.lower().endswith('.png'):
            category_folder = os.path.basename(root)
            name_part = filename.rsplit('.', 1)[0]
            images_by_category[category_folder].append((name_part, filename))
            all_images[name_part] = (category_folder, filename)

print("\n" + "=" * 80)
print("📊 ITEM-IMAGE MAPPING VALIDATION REPORT")
print("=" * 80)

# Verify all items have images
missing_images = []
matched_images = []
orphaned_images = []

for display_name, (item_id, item_type) in name_to_item.items():
    if display_name in all_images:
        category, filename = all_images[display_name]
        matched_images.append((item_id, display_name, category, filename))
        print(f"✓ {item_id:30} → {display_name:25} → {filename}")
    else:
        missing_images.append((item_id, display_name))
        print(f"✗ {item_id:30} → {display_name:25} → MISSING IMAGE")

# Check for orphaned images
for display_name, (category, filename) in all_images.items():
    if display_name not in name_to_item:
        orphaned_images.append((display_name, category, filename))
        print(f"⚠ ORPHANED IMAGE: {category}/{filename}")

print("\n" + "=" * 80)
print("📈 SUMMARY")
print("=" * 80)
print(f"Total items in game:       {len(items_data)}")
print(f"Items with images:         {len(matched_images)} ✓")
print(f"Items missing images:      {len(missing_images)} ✗")
print(f"Orphaned images:           {len(orphaned_images)} ⚠")

if missing_images:
    print("\n❌ Missing images:")
    for item_id, display_name in missing_images:
        print(f"   - {item_id}: {display_name}")

if orphaned_images:
    print("\n⚠️  Orphaned images (no matching item):")
    for display_name, category, filename in orphaned_images:
        print(f"   - {category}/{filename}")

print("\n" + "=" * 80)
print("📁 IMAGE INVENTORY BY CATEGORY")
print("=" * 80)

for category in sorted(images_by_category.keys()):
    images = images_by_category[category]
    print(f"\n{category}/ ({len(images)} images)")
    for name_part, filename in sorted(images):
        status = "✓" if name_part in name_to_item else "⚠"
        print(f"  {status} {filename}")

print("\n" + "=" * 80)
if len(missing_images) == 0 and len(orphaned_images) == 0:
    print("✅ ALL ITEMS PROPERLY MAPPED TO IMAGES - NO ISSUES FOUND!")
else:
    print("⚠️  Please review the issues listed above")
print("=" * 80 + "\n")
