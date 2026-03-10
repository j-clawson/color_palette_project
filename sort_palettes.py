import pandas as pd
import numpy as np
import re

def parse_rgb(rgb_str):
    """Parse RGB string like '(228, 232, 241)' to tuple"""
    rgb_str = rgb_str.strip('()')
    return tuple(map(int, rgb_str.split(', ')))

def rgb_brightness(rgb):
    """Calculate brightness as Euclidean distance from (0,0,0)"""
    r, g, b = rgb
    return np.sqrt(r**2 + g**2 + b**2)

# Read the original CSV
df = pd.read_csv('monet_full_palettes.csv')

# Prepare output data
output_data = []

for idx, row in df.iterrows():
    filename = row['filename']
    
    # Collect RGB tuples and their brightness
    colors = []
    for i in range(1, 6):
        rgb_str = row[f'color_{i}_rgb']
        rgb = parse_rgb(rgb_str)
        brightness = rgb_brightness(rgb)
        colors.append((rgb, brightness))
    
    # Sort by brightness (darkest first)
    colors.sort(key=lambda x: x[1])
    
    # Create new row with sorted RGB strings
    new_row = {'filename': filename}
    for i, (rgb, _) in enumerate(colors, 1):
        rgb_str = f"({rgb[0]}, {rgb[1]}, {rgb[2]})"
        new_row[f'color_{i}_rgb'] = rgb_str
    
    output_data.append(new_row)

# Create new DataFrame and save
output_df = pd.DataFrame(output_data)
output_df.to_csv('sorted_monet_palettes.csv', index=False)

print("Sorted palettes saved to sorted_monet_palettes.csv")
print(f"Processed {len(output_df)} paintings")