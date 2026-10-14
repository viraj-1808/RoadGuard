#!/usr/bin/env python3
"""
Read-only script to scan all training and validation images
in experiments/dataset/experiment2/images/ and report dimension statistics,
payload calculations, and cache estimates.
"""

import os
from PIL import Image
from collections import Counter

def get_image_files(directory):
    """Get all image files in a directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file.lower())[1] in image_extensions:
                image_files.append(os.path.join(root, file))
    
    return image_files

def process_image(image_path):
    """Process a single image and return its properties."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            return {
                'width': width,
                'height': height,
                'mode': img.mode
            }
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def calculate_statistics(values):
    """Calculate statistics for a list of values."""
    if not values:
        return {
            'count': 0,
            'min': None,
            'max': None,
            'mean': None,
            'median': None,
            'mode': None
        }
    
    sorted_values = sorted(values)
    count = len(values)
    min_val = min(values)
    max_val = max(values)
    mean_val = sum(values) / count
    
    # Median
    if count % 2 == 0:
        median_val = (sorted_values[count//2 - 1] + sorted_values[count//2]) / 2
    else:
        median_val = sorted_values[count//2]
    
    # Mode
    counter = Counter(values)
    mode_val = counter.most_common(1)[0][0] if counter else None
    
    return {
        'count': count,
        'min': min_val,
        'max': max_val,
        'mean': mean_val,
        'median': median_val,
        'mode': mode_val
    }

def calculate_payload_and_cache(width, height, imgsz=640):
    """Calculate payload and cache estimates for an image.
    
    Original payload: h × w × 3 × 1 byte
    Resized cache at imgsz=640: long side = 640, aspect ratio preserved
    """
    # Original payload
    payload = width * height * 3
    
    # Resized cache estimate at imgsz=640
    if width >= height:
        new_width = imgsz
        new_height = int((imgsz * height) / width)
    else:
        new_height = imgsz
        new_width = int((imgsz * width) / height)
    
    cache_size = new_width * new_height * 3
    
    return payload, cache_size

def analyze_directory(directory_path, dir_name):
    """Analyze all images in a directory and return statistics."""
    print(f"\n=== Analyzing {dir_name} directory: {directory_path} ===")
    
    image_files = get_image_files(directory_path)
    print(f"Found {len(image_files)} image files")
    
    if not image_files:
        print("No image files found!")
        return None
    
    # Initialize lists to store dimensions
    widths = []
    heights = []
    modes = []
    
    total_payload = 0
    total_cache = 0
    
    # Process each image one at a time
    for i, image_path in enumerate(image_files):
        result = process_image(image_path)
        if result is None:
            continue
            
        widths.append(result['width'])
        heights.append(result['height'])
        modes.append(result['mode'])
        
        # Calculate payload and cache
        payload, cache = calculate_payload_and_cache(result['width'], result['height'])
        total_payload += payload
        total_cache += cache
        
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(image_files)} images...")
    
    print(f"  Finished processing {len(image_files)} images")
    
    # Calculate statistics for widths and heights
    width_stats = calculate_statistics(widths)
    height_stats = calculate_statistics(heights)
    
    # Check mode consistency
    mode_counter = Counter(modes)
    primary_mode = mode_counter.most_common(1)[0][0] if mode_counter else None
    mode_consistent = len(mode_counter) <= 1
    
    return {
        'directory': directory_path,
        'dir_name': dir_name,
        'image_count': len(image_files),
        'width_stats': width_stats,
        'height_stats': height_stats,
        'mode_consistent': mode_consistent,
        'primary_mode': primary_mode,
        'total_payload': total_payload,
        'total_cache': total_cache
    }

def main():
    """Main function to run the image analysis."""
    base_path = r"C:\Users\viraj\Code_files\Github\RoadGuard AI\experiments\dataset\experiment2\images"
    
    print("RoadGuard AI Image Dataset Analyzer")
    print("=" * 50)
    
    # Analyze train directory
    train_dir = os.path.join(base_path, "train")
    train_results = analyze_directory(train_dir, "train")
    
    # Analyze val directory
    val_dir = os.path.join(base_path, "val")
    val_results = analyze_directory(val_dir, "val")
    
    # Print results
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    
    if train_results:
        print(f"\nTRAIN DIRECTORY:")
        print(f"  Image count: {train_results['image_count']}")
        print(f"  Width stats: min={train_results['width_stats']['min']}, max={train_results['width_stats']['max']}, "
              f"mean={train_results['width_stats']['mean']:.1f}, median={train_results['width_stats']['median']:.1f}, "
              f"mode={train_results['width_stats']['mode']}")
        print(f"  Height stats: min={train_results['height_stats']['min']}, max={train_results['height_stats']['max']}, "
              f"mean={train_results['height_stats']['mean']:.1f}, median={train_results['height_stats']['median']:.1f}, "
              f"mode={train_results['height_stats']['mode']}")
        print(f"  Mode: {train_results['primary_mode']} (consistent: {train_results['mode_consistent']})")
        print(f"  Total decoded payload: {train_results['total_payload']:,} bytes ({train_results['total_payload'] / (1024**2):.2f} MB)")
        print(f"  Estimated RAM cache (imgsz=640): {train_results['total_cache']:,} bytes ({train_results['total_cache'] / (1024**2):.2f} MB)")
    
    if val_results:
        print(f"\nVALIDATION DIRECTORY:")
        print(f"  Image count: {val_results['image_count']}")
        print(f"  Width stats: min={val_results['width_stats']['min']}, max={val_results['width_stats']['max']}, "
              f"mean={val_results['width_stats']['mean']:.1f}, median={val_results['width_stats']['median']:.1f}, "
              f"mode={val_results['width_stats']['mode']}")
        print(f"  Height stats: min={val_results['height_stats']['min']}, max={val_results['height_stats']['max']}, "
              f"mean={val_results['height_stats']['mean']:.1f}, median={val_results['height_stats']['median']:.1f}, "
              f"mode={val_results['height_stats']['mode']}")
        print(f"  Mode: {val_results['primary_mode']} (consistent: {val_results['mode_consistent']})")
        print(f"  Total decoded payload: {val_results['total_payload']:,} bytes ({val_results['total_payload'] / (1024**2):.2f} MB)")
        print(f"  Estimated RAM cache (imgsz=640): {val_results['total_cache']:,} bytes ({val_results['total_cache'] / (1024**2):.2f} MB)")
    
    if train_results and val_results:
        combined_payload = train_results['total_payload'] + val_results['total_payload']
        combined_cache = train_results['total_cache'] + val_results['total_cache']
        print(f"\nCOMBINED TOTALS:")
        print(f"  Total images: {train_results['image_count'] + val_results['image_count']}")
        print(f"  Combined decoded payload: {combined_payload:,} bytes ({combined_payload / (1024**2):.2f} MB)")
        print(f"  Combined estimated RAM cache (imgsz=640): {combined_cache:,} bytes ({combined_cache / (1024**2):.2f} MB)")


if __name__ == "__main__":
    main()