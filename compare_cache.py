import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import argparse
import re


def parse_cache_file(file_path):
    """Parse the cache file and extract benchmark data."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    benchmarks = {}
    current_bench = None
    
    for line in lines[1:]:  # Skip header
        line = line.strip()
        if not line:
            continue
        
        parts = line.split(',')
        
        # Check if this is a benchmark name line
        if len(parts) <= 2 and parts[0].strip():
            # Extract benchmark name without suffix (ignore after underscore)
            bench_name = parts[0].split('_')[0]
            current_bench = bench_name
            benchmarks[current_bench] = {}
        elif current_bench and len(parts) >= 3:
            # This is a statistic line
            stat_name = parts[0]
            
            # Handle total value - some might not be numeric
            try:
                total = float(parts[1])
            except ValueError:
                total = 0
            
            # Handle percentage value - some might have % sign
            if parts[2].endswith('%'):
                percentage = float(parts[2].rstrip('%'))
            else:
                try:
                    percentage = float(parts[2])
                except ValueError:
                    percentage = 0
                    
            benchmarks[current_bench][stat_name] = {
                'total': total,
                'percentage': percentage
            }
            
    return benchmarks


def plot_comparison(file1_data, file2_data, file1_name, file2_name, stat_to_plot="Cache Hits", use_percentage=True, show_difference=False):
    """Create a bar chart comparing the two data sets with enhancements for small differences."""
    benchmarks = list(set(file1_data.keys()) & set(file2_data.keys()))
    benchmarks.sort()
    
    if not benchmarks:
        print("No common benchmarks found between the files.")
        return
    
    orange = (0.9882, 0.4627, 0.2039)
    green = (0.1216, 0.8157, 0.5098)

    # Prepare data for plotting
    values1 = []
    values2 = []
    differences = []
    
    for bench in benchmarks:
        if stat_to_plot in file1_data[bench]:
            if use_percentage:
                values1.append(file1_data[bench][stat_to_plot]['percentage'])
            else:
                values1.append(file1_data[bench][stat_to_plot]['total'])
        else:
            values1.append(0)
            
        if stat_to_plot in file2_data[bench]:
            if use_percentage:
                values2.append(file2_data[bench][stat_to_plot]['percentage'])
            else:
                values2.append(file2_data[bench][stat_to_plot]['total'])
        else:
            values2.append(0)
        
        # Calculate differences for potential analysis
        differences.append(values2[-1] - values1[-1])
    
    # Create a single plot instead of subplots
    fig, ax = plt.subplots(figsize=(14, 8))
    
    x = np.arange(len(benchmarks))
    width = 0.35
    
    # Create the comparison plot
    rects1 = ax.bar(x - width/2, values1, width, label=file1_name, color=green, alpha=0.8)
    rects2 = ax.bar(x + width/2, values2, width, label=file2_name, color=orange, alpha=0.8)
    
    # Add value labels on top of each bar
    def add_labels(rects, ax):
        for rect in rects:
            height = rect.get_height()
            value_text = f"{height:.2f}"
            if use_percentage:
                value_text = f"{height:.1f}%"
            ax.annotate(value_text,
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', 
                        fontsize=8, rotation=45)
    
    add_labels(rects1, ax)
    add_labels(rects2, ax)
    
    # Customize the plot
    y_label = f"{stat_to_plot} ({'%' if use_percentage else 'Total'})"
    ax.set_ylabel(y_label, fontweight='bold')
    ax.set_title(f'Comparison of {stat_to_plot} between {file1_name} and {file2_name}', fontweight='bold')
    ax.set_xticks(x)
    
    # Display benchmark names on the x-axis
    ax.set_xticklabels(benchmarks, rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Calculate good y limits based on data range
    values_min = min(min(values1), min(values2))
    values_max = max(max(values1), max(values2))
    padding = (values_max - values_min) * 0.1
    ax.set_ylim(max(0, values_min - padding), values_max + padding)
    
    # Check if we have very small differences and need to zoom in
    if values_max > 0 and all(abs(diff) / values_max < 0.1 for diff in differences):
        # Add a zoomed-in inset to highlight small differences
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        axins = inset_axes(ax, width="40%", height="30%", loc="upper left")
        axins.bar(x - width/2, values1, width, color=green, alpha=0.8)
        axins.bar(x + width/2, values2, width, color=orange, alpha=0.8)
        
        # Set y-limits for the zoomed region
        zoom_min = min(min(values1), min(values2))
        zoom_max = max(max(values1), max(values2))
        zoom_padding = (zoom_max - zoom_min) * 0.1
        zoom_min = max(0, zoom_min - zoom_padding)
        zoom_range = zoom_max - zoom_min
        axins.set_ylim(zoom_min, zoom_min + zoom_range * 0.3)  # Show top 30% of the data
        axins.set_xticklabels([])
        axins.set_title("Zoomed View", fontsize=8)
        axins.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout to prevent overlapping
    fig.tight_layout()
    
    # Save the figure with higher quality
    output_filename = f"{stat_to_plot.replace(' ', '_')}_comparison.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Enhanced plot saved as {output_filename}")


def main():
    parser = argparse.ArgumentParser(description='Compare cache statistics between two CSV files.')
    parser.add_argument('file1', help='First cache CSV file')
    parser.add_argument('file2', help='Second cache CSV file')
    parser.add_argument('--name1', help='Label for first file', default='File 1')
    parser.add_argument('--name2', help='Label for second file', default='File 2')
    parser.add_argument('--stat', help='Statistic to plot', default='Cache Hits')
    parser.add_argument('--percentage', help='Use percentage (true) or total (false)', 
                        type=lambda x: (str(x).lower() == 'true'), default=True)
    
    args = parser.parse_args()
    
    # Parse the cache files
    file1_data = parse_cache_file(args.file1)
    file2_data = parse_cache_file(args.file2)
    
    # Plot the comparison
    plot_comparison(file1_data, file2_data, args.name1, args.name2, args.stat, args.percentage)
    
    # Also generate plots for other common statistics
    common_stats = ['Cache Misses', 'Evictions Capacity']
    for stat in common_stats:
        if stat != args.stat:
            plot_comparison(file1_data, file2_data, args.name1, args.name2, stat, args.percentage)


if __name__ == "__main__":
    main()