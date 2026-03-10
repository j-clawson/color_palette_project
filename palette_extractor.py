import os
import csv
import argparse
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

def rgb_to_hex(rgb):
    """Converts an RGB tuple to a hex string."""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def rgb_to_cmyk(rgb):
    """
    Converts an RGB tuple (0-255) to a CMYK tuple (0-100%).
    Formula:
    K = 1 - max(R', G', B')
    C = (1 - R' - K) / (1 - K)
    M = (1 - G' - K) / (1 - K)
    Y = (1 - B' - K) / (1 - K)
    """
    r, g, b = [x / 255.0 for x in rgb]
    k = 1 - max(r, g, b)
    if k == 1:
        return (0, 0, 0, 100)
    
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    
    return tuple(round(x * 100) for x in [c, m, y, k])

def extract_palette(image_path, n_colors=5, resize=(200, 200), palette_formats=['hex', 'rgb']):
    """
    Extracts the dominant colors from an image using KMeans clustering.
    Returns a list of dictionaries containing the requested formats.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img = img.resize(resize)
        img_array = np.array(img)
        
        # Flatten pixels
        pixels = img_array.reshape(-1, 3)
        
        # KMeans clustering
        kmeans = KMeans(n_clusters=n_colors, n_init=10, random_state=42)
        labels = kmeans.fit_predict(pixels)
        
        colors = kmeans.cluster_centers_.astype(int)
        
        # Compute proportions to sort by dominance
        counts = np.bincount(labels)
        proportions = counts / counts.sum()
        
        # Sort by most common color
        order = np.argsort(proportions)[::-1]
        sorted_colors = colors[order]
        
        extracted = []
        for color in sorted_colors:
            color_data = {}
            rgb = tuple(map(int, color))
            if 'hex' in palette_formats:
                color_data['hex'] = rgb_to_hex(rgb)
            if 'rgb' in palette_formats:
                color_data['rgb'] = rgb
            if 'cmyk' in palette_formats:
                color_data['cmyk'] = rgb_to_cmyk(rgb)
            extracted.append(color_data)
            
        return extracted
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Extract color palettes from a folder of images and save to CSV.")
    parser.add_argument("input_folder", help="Path to the folder containing images.")
    parser.add_argument("--output", "-o", default="color_palettes.csv", help="Path to the output CSV file.")
    parser.add_argument("--colors", "-c", type=int, default=5, help="Number of dominant colors to extract.")
    parser.add_argument("--formats", "-f", nargs="+", default=['hex', 'rgb'], 
                        choices=['hex', 'rgb', 'cmyk'], help="Color formats to include in the output.")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.input_folder):
        print(f"Error: {args.input_folder} is not a valid directory.")
        return

    # Supported image extensions
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp')
    image_files = [f for f in os.listdir(args.input_folder) 
                   if f.lower().endswith(valid_extensions) and not f.startswith('._')]
    
    if not image_files:
        print(f"No valid image files found in {args.input_folder}.")
        return

    print(f"Found {len(image_files)} images. Starting palette extraction...")
    print(f"Formats: {', '.join(args.formats)}")

    # Prepare CSV header
    header = ['filename']
    for i in range(args.colors):
        for fmt in args.formats:
            header.append(f'color_{i+1}_{fmt}')
    
    results = []
    for i, filename in enumerate(image_files):
        img_path = os.path.join(args.input_folder, filename)
        print(f"[{i+1}/{len(image_files)}] Processing: {filename}")
        
        palette = extract_palette(img_path, n_colors=args.colors, palette_formats=args.formats)
        if palette:
            row = [filename]
            for color_data in palette:
                for fmt in args.formats:
                    # Store as string for CSV
                    val = color_data.get(fmt)
                    row.append(str(val) if val is not None else "")
            
            # Fill remaining columns if fewer colors were found
            expected_len = 1 + (args.colors * len(args.formats))
            if len(row) < expected_len:
                row.extend([""] * (expected_len - len(row)))
                
            results.append(row)

    # Save to CSV
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)

    print(f"\nDone! Extracted palettes for {len(results)} images.")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
