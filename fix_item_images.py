import os
import json
import shutil
from pathlib import Path

# Define paths
WORKSPACE_ROOT = r"d:\Void_frontier_Project\Void_frontier"
ITEMS_JSON = os.path.join(WORKSPACE_ROOT, "data", "items.json")
ITEMS_IMG_DIR = os.path.join(WORKSPACE_ROOT, "assets", "images", "items")

# Load items.json
with open(ITEMS_JSON, 'r', encoding='utf-8') as f:
    items_data = json.load(f)

# Create mapping of display names to item IDs
name_to_id = {}
for item_id, item_info in items_data.items():
    display_name = item_info.get('name', '')
    name_to_id[display_name] = item_id

print("🔧 Item Image File Renaming Tool")
print("=" * 60)
print(f"\nScanning: {ITEMS_IMG_DIR}")
print()

rename_count = 0
issues_fixed = []

# Walk through all subdirectories
for root, dirs, files in os.walk(ITEMS_IMG_DIR):
    for filename in files:
        if filename.lower().endswith('.png'):
            old_path = os.path.join(root, filename)
            category = os.path.basename(root)
            
            # Clean up whitespace in filename
            cleaned_name = filename.strip()
            
            # Check for leading/trailing spaces
            if cleaned_name != filename:
                new_path = os.path.join(root, cleaned_name)
                print(f"✓ Fixed whitespace: '{filename}' → '{cleaned_name}'")
                shutil.move(old_path, new_path)
                issues_fixed.append(f"{category}: {filename}")
                rename_count += 1
                filename = cleaned_name
                old_path = new_path
            
            # Verify the image matches an item
            name_part = filename.rsplit('.', 1)[0]  # Remove .png
            if name_part in name_to_id:
                print(f"  ✓ Verified: '{filename}' → item '{name_to_id[name_part]}'")
            else:
                print(f"  ⚠ Warning: No item found for '{filename}'")

print("\n" + "=" * 60)
if issues_fixed:
    print(f"\n✅ Fixed {rename_count} file(s) with whitespace issues:")
    for issue in issues_fixed:
        print(f"   - {issue}")
else:
    print("\n✅ All files are properly formatted!")

print("\n📁 Current Item Image Structure:")
print("=" * 60)
for root, dirs, files in os.walk(ITEMS_IMG_DIR):
    level = root.replace(ITEMS_IMG_DIR, '').count(os.sep)
    indent = ' ' * 2 * level
    category = os.path.basename(root)
    if category == 'items':
        category = "Items"
    file_count = len([f for f in files if f.lower().endswith('.png')])
    if file_count > 0:
        print(f"{indent}{category}/ ({file_count} images)")
        subindent = ' ' * 2 * (level + 1)
        for f in sorted([f for f in files if f.lower().endswith('.png')]):
            print(f"{subindent}• {f}")

print("\n" + "=" * 60)
print("✨ Item image organization complete!")
