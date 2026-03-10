import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import argparse
import os
import ast
import numpy as np

def load_data(csv_path):
    """Loads the color palette data from CSV."""
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found.")
        return None
    
    df = pd.read_csv(csv_path)
    # Parse RGB strings back into tuples if they exist
    for col in df.columns:
        if '_rgb' in col:
            df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    return df

def plot_palette_summary(df, output_path, limit=50):
    """Creates a summary visualization of multiple palettes."""
    df_subset = df.head(limit)
    num_paintings = len(df_subset)
    
    fig, ax = plt.subplots(figsize=(12, num_paintings * 0.4))
    
    for i, row in df_subset.iterrows():
        # Get hex colors
        hex_cols = [col for col in df.columns if '_hex' in col]
        colors = [row[col] for col in hex_cols]
        
        # Create a horizontal bar for each painting
        start = 0
        for color in colors:
            ax.barh(i, 1.0, left=start, color=color, edgecolor='none', height=0.8)
            start += 1.0
            
    ax.set_yticks(range(num_paintings))
    ax.set_yticklabels(df_subset['filename'], fontsize=8)
    ax.invert_yaxis()
    ax.set_title(f"Color Palette Summary (Top {num_paintings} Paintings)", fontsize=14, pad=20)
    ax.set_xlabel("Colors")
    ax.set_xticks([])
    
    plt.tight_layout()
    plt.savefig(output_path)
    print(f"Saved summary plot to {output_path}")
    plt.close()

def plot_interactive_dashboard(df, output_path):
    """Creates an interactive plotly visualization."""
    # Reshape data for plotly
    all_colors = []
    for _, row in df.iterrows():
        for i in range(1, 6):
            all_colors.append({
                'painting': row['filename'],
                'color_index': f'Color {i}',
                'hex': row[f'color_{i}_hex'],
                'rgb': str(row[f'color_{i}_rgb'])
            })
    
    plot_df = pd.DataFrame(all_colors)
    
    fig = px.strip(plot_df, 
                   x="color_index", 
                   y="painting", 
                   color="hex",
                   color_discrete_map={h: h for h in plot_df['hex'].unique()},
                   title="Interactive Color Distribution",
                   hover_data=["hex", "rgb"])
    
    fig.update_layout(
        showlegend=False,
        height=len(df) * 15 + 200, # Dynamic height
        template="plotly_dark"
    )
    
    fig.write_html(output_path)
    print(f"Saved interactive dashboard to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Visualize extracted color palettes.")
    parser.add_argument("--input", type=str, default="monet_full_palettes.csv", help="Path to input CSV.")
    parser.add_argument("--output_dir", type=str, default="plots", help="Directory to save plots.")
    parser.add_argument("--type", type=str, choices=["summary", "interactive", "all"], default="all", help="Type of visualization.")
    parser.add_argument("--limit", type=int, default=50, help="Number of paintings for summary plot.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    df = load_data(args.input)
    if df is None:
        return

    if args.type in ["summary", "all"]:
        summary_out = os.path.join(args.output_dir, "palette_summary.png")
        plot_palette_summary(df, summary_out, limit=args.limit)
        
    if args.type in ["interactive", "all"]:
        interactive_out = os.path.join(args.output_dir, "palette_dashboard.html")
        plot_interactive_dashboard(df, interactive_out)

if __name__ == "__main__":
    main()
