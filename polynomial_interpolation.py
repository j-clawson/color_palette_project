import pandas as pd
import numpy as np

# Read the CSV file
df = pd.read_csv('sorted_monet_palettes.csv')

# Function to parse RGB string to tuple
def parse_rgb(rgb_str):
    rgb_str = rgb_str.strip('()')
    return tuple(map(int, rgb_str.split(', ')))

# Prepare output data
output_data = []

for idx, row in df.iterrows():
    filename = row['filename']
    colors = []
    for i in range(1, 6):
        rgb_str = row[f'color_{i}_rgb']
        rgb = parse_rgb(rgb_str)
        colors.append(rgb)
    
    # Extract R, G, B values
    x = np.array([1, 2, 3, 4, 5])
    r_values = np.array([c[0] for c in colors])
    g_values = np.array([c[1] for c in colors])
    b_values = np.array([c[2] for c in colors])
    
    # Fit polynomials of degree 4
    r_coeffs = np.polyfit(x, r_values, 4)
    g_coeffs = np.polyfit(x, g_values, 4)
    b_coeffs = np.polyfit(x, b_values, 4)
    
    # Combine coefficients (from highest to lowest degree)
    coeffs = list(r_coeffs) + list(g_coeffs) + list(b_coeffs)
    output_data.append([filename] + coeffs)

# Create output DataFrame
columns = ['filename'] + [f'r_coeff{i}' for i in range(5)] + [f'g_coeff{i}' for i in range(5)] + [f'b_coeff{i}' for i in range(5)]
output_df = pd.DataFrame(output_data, columns=columns)

# Save to CSV
output_df.to_csv('monet_polynomial_coefficients.csv', index=False)

print("Polynomial interpolation completed. Coefficients saved to monet_polynomial_coefficients.csv")