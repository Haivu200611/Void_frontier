"""
Item Mapping Analyzer
Analyzes the mapping between items.json and image files in assets/images/items/
Provides a detailed report on asset-item consistency and standardization.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set


class ItemMappingAnalyzer:
    def __init__(self, items_json_path: str, images_dir_path: str):
        self.items_json_path = items_json_path
        self.images_dir_path = images_dir_path
        
        self.items_data = {}
        self.image_files = defaultdict(list)
        self.all_image_files = []
        
        self.results = {
            'matched': [],
            'missing_images': [],
            'mismatched_names': [],
            'orphaned_images': [],
            'standardization_suggestions': []
        }
    
    def load_items_json(self) -> bool:
        """Load and parse items.json"""
        try:
            with open(self.items_json_path, 'r', encoding='utf-8') as f:
                self.items_data = json.load(f)
            print(f"✓ Loaded {len(self.items_data)} items from items.json")
            return True
        except Exception as e:
            print(f"✗ Error loading items.json: {e}")
            return False
    
    def scan_image_directory(self) -> bool:
        """Scan the images directory for all item images"""
        try:
            images_path = Path(self.images_dir_path)
            
            if not images_path.exists():
                print(f"✗ Images directory not found: {self.images_dir_path}")
                return False
            
            # Scan all subdirectories
            for root, dirs, files in os.walk(images_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        rel_path = os.path.relpath(os.path.join(root, file), images_path)
                        category = os.path.dirname(rel_path)
                        self.image_files[category].append(file)
                        self.all_image_files.append(file)
            
            print(f"✓ Found {len(self.all_image_files)} image files")
            return True
        except Exception as e:
            print(f"✗ Error scanning images directory: {e}")
            return False
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for comparison"""
        return name.strip().lower()
    
    def find_matching_image(self, item_name: str, item_id: str) -> Tuple[bool, str, str]:
        """
        Find a matching image file for an item
        Returns: (found, image_path, category)
        """
        normalized_item_name = self.normalize_name(item_name)
        
        # Check exact match (normalized)
        for image_file in self.all_image_files:
            if self.normalize_name(image_file.rsplit('.', 1)[0]) == normalized_item_name:
                # Find which category it belongs to
                for category, files in self.image_files.items():
                    if image_file in files:
                        return True, image_file, category
        
        # No exact match found
        return False, None, None
    
    def suggest_standardized_name(self, item_id: str, item_name: str, item_type: str) -> str:
        """
        Suggest a standardized filename based on item ID and name
        Format: {item_id}_{display_name}.png
        """
        # Create a clean filename from item_id and name
        clean_id = item_id.replace('item_', '').replace('_', '-')
        clean_name = item_name.lower().replace(' ', '-')
        
        # Combine for standardized name
        suggested = f"{clean_id}_{clean_name}.png"
        return suggested
    
    def analyze_mapping(self):
        """Analyze the mapping between items and images"""
        print("\n" + "="*80)
        print("ANALYZING ITEM-IMAGE MAPPING")
        print("="*80 + "\n")
        
        matched_images = set()
        
        for item_id, item_info in self.items_data.items():
            item_name = item_info.get('name', 'Unknown')
            item_type = item_info.get('type', 'unknown')
            
            found, image_file, category = self.find_matching_image(item_name, item_id)
            
            if found:
                self.results['matched'].append({
                    'item_id': item_id,
                    'item_name': item_name,
                    'item_type': item_type,
                    'image_file': image_file,
                    'category': category
                })
                matched_images.add(image_file)
            else:
                self.results['missing_images'].append({
                    'item_id': item_id,
                    'item_name': item_name,
                    'item_type': item_type,
                    'suggested_filename': self.suggest_standardized_name(item_id, item_name, item_type)
                })
        
        # Find orphaned images
        for image_file in self.all_image_files:
            if image_file not in matched_images:
                # Find which category it belongs to
                for category, files in self.image_files.items():
                    if image_file in files:
                        self.results['orphaned_images'].append({
                            'image_file': image_file,
                            'category': category,
                            'possible_item_id': self._find_possible_item_id(image_file)
                        })
                        break
        
        # Generate standardization suggestions for all items
        for item_id, item_info in self.items_data.items():
            item_name = item_info.get('name', 'Unknown')
            item_type = item_info.get('type', 'unknown')
            
            suggestion = self.suggest_standardized_name(item_id, item_name, item_type)
            self.results['standardization_suggestions'].append({
                'item_id': item_id,
                'current_name': item_name,
                'suggested_filename': suggestion
            })
    
    def _find_possible_item_id(self, image_file: str) -> str:
        """Try to find which item an orphaned image might belong to"""
        clean_filename = image_file.rsplit('.', 1)[0].strip().lower()
        
        for item_id, item_info in self.items_data.items():
            item_name = item_info.get('name', '').lower()
            if item_name and item_name in clean_filename:
                return item_id
        
        return None
    
    def print_report(self):
        """Print the analysis report"""
        print("\n" + "="*80)
        print("ITEM MAPPING ANALYSIS REPORT")
        print("="*80)
        
        # Summary
        print("\n📊 SUMMARY")
        print("-" * 80)
        total_items = len(self.items_data)
        matched = len(self.results['matched'])
        missing = len(self.results['missing_images'])
        orphaned = len(self.results['orphaned_images'])
        match_percentage = (matched / total_items * 100) if total_items > 0 else 0
        
        print(f"Total items in JSON:        {total_items}")
        print(f"Items with matching images: {matched} ({match_percentage:.1f}%)")
        print(f"Items missing images:       {missing}")
        print(f"Orphaned images:            {orphaned}")
        
        # Matched items
        print("\n" + "="*80)
        print("✓ ITEMS WITH CORRECTLY NAMED IMAGES ({})".format(len(self.results['matched'])))
        print("="*80)
        
        if self.results['matched']:
            # Group by type
            by_type = defaultdict(list)
            for item in self.results['matched']:
                by_type[item['item_type']].append(item)
            
            for item_type in sorted(by_type.keys()):
                items = by_type[item_type]
                print(f"\n  {item_type.upper()} ({len(items)})")
                print("  " + "-" * 76)
                for item in sorted(items, key=lambda x: x['item_id']):
                    print(f"    ✓ {item['item_id']:35} → {item['image_file']:30} ({item['category']})")
        
        # Missing images
        print("\n" + "="*80)
        print("✗ ITEMS MISSING IMAGES ({})".format(len(self.results['missing_images'])))
        print("="*80)
        
        if self.results['missing_images']:
            by_type = defaultdict(list)
            for item in self.results['missing_images']:
                by_type[item['item_type']].append(item)
            
            for item_type in sorted(by_type.keys()):
                items = by_type[item_type]
                print(f"\n  {item_type.upper()} ({len(items)})")
                print("  " + "-" * 76)
                for item in sorted(items, key=lambda x: x['item_id']):
                    print(f"    ✗ {item['item_id']:35} → {item['item_name']}")
                    print(f"      💡 Suggested filename: {item['suggested_filename']}")
        else:
            print("\n  ✓ All items have matching images!")
        
        # Orphaned images
        print("\n" + "="*80)
        print("🗂️  ORPHANED IMAGES ({})".format(len(self.results['orphaned_images'])))
        print("="*80)
        
        if self.results['orphaned_images']:
            by_category = defaultdict(list)
            for image in self.results['orphaned_images']:
                by_category[image['category']].append(image)
            
            for category in sorted(by_category.keys()):
                images = by_category[category]
                print(f"\n  {category} ({len(images)})")
                print("  " + "-" * 76)
                for image in sorted(images, key=lambda x: x['image_file']):
                    possible_id = image['possible_item_id'] or "Unknown"
                    print(f"    🔍 {image['image_file']:40} → Possible: {possible_id}")
        else:
            print("\n  ✓ No orphaned images found!")
        
        # Standardization suggestions
        print("\n" + "="*80)
        print("💾 STANDARDIZATION SUGGESTIONS")
        print("="*80)
        print("\nRecommended standardized filenames for all items:")
        print("(Format: {item_id}_{display_name}.png)\n")
        
        by_type = defaultdict(list)
        for item in self.results['standardization_suggestions']:
            # Extract type from item_id or use a category
            if 'weapon' in item['item_id']:
                item_type = 'Weapon & Ammo'
            elif 'tool' in item['item_id'] or 'upgrade' in item['item_id']:
                item_type = 'Tools & Upgrades'
            elif 'quest' in item['item_id']:
                item_type = 'Quest Items'
            elif 'medkit' in item['item_id'] or 'oxygen' in item['item_id'] or 'food' in item['item_id']:
                item_type = 'Consumables'
            elif 'ammo' in item['item_id']:
                item_type = 'Weapon & Ammo'
            else:
                item_type = 'Crafting Resource'
            
            by_type[item_type].append(item)
        
        for category in sorted(by_type.keys()):
            items = by_type[category]
            print(f"  {category}")
            print("  " + "-" * 76)
            for item in sorted(items, key=lambda x: x['item_id']):
                print(f"    {item['suggested_filename']:40} ({item['item_id']})")
    
    def run(self) -> bool:
        """Run the complete analysis"""
        print("Starting Item Mapping Analysis...\n")
        
        if not self.load_items_json():
            return False
        
        if not self.scan_image_directory():
            return False
        
        self.analyze_mapping()
        self.print_report()
        
        return True


def main():
    # Define paths
    project_root = r"d:\Void_frontier_Project\Void_frontier"
    items_json = os.path.join(project_root, "data", "items.json")
    images_dir = os.path.join(project_root, "assets", "images", "items")
    
    # Create analyzer and run
    analyzer = ItemMappingAnalyzer(items_json, images_dir)
    success = analyzer.run()
    
    if success:
        print("\n" + "="*80)
        print("Analysis complete!")
        print("="*80 + "\n")
    else:
        print("\n✗ Analysis failed!")


if __name__ == "__main__":
    main()
