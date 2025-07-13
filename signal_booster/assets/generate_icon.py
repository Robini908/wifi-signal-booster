"""
Script to generate an icon for the Signal Booster application.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def generate_signal_booster_icon(output_path="icon.png", size=(256, 256)):
    """Generate a simple signal booster icon."""
    # Create a new image with transparent background
    img = Image.new('RGBA', size, color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Calculate dimensions
    width, height = size
    center_x, center_y = width // 2, height // 2
    min_dim = min(width, height)
    outer_radius = int(min_dim * 0.45)
    inner_radius = int(min_dim * 0.35)
    
    # Draw the outer circle (blue)
    draw.ellipse(
        (center_x - outer_radius, center_y - outer_radius,
         center_x + outer_radius, center_y + outer_radius),
        fill="#1976D2"
    )
    
    # Draw the inner circle (darker blue)
    draw.ellipse(
        (center_x - inner_radius, center_y - inner_radius,
         center_x + inner_radius, center_y + inner_radius),
        fill="#0D47A1"
    )
    
    # Draw signal bars
    bar_width = int(min_dim * 0.08)
    bar_spacing = int(bar_width * 0.5)
    bar_start_x = center_x - (bar_width * 2 + bar_spacing * 1.5)
    bar_base_y = center_y + int(min_dim * 0.1)
    
    bar_heights = [
        int(min_dim * 0.15),  # Short bar
        int(min_dim * 0.25),  # Medium bar
        int(min_dim * 0.35),  # Tall bar
        int(min_dim * 0.45),  # Tallest bar
    ]
    
    bar_colors = ["#FF5252", "#FFAB40", "#69F0AE", "#FFFFFF"]
    
    for i, (height, color) in enumerate(zip(bar_heights, bar_colors)):
        x = bar_start_x + i * (bar_width + bar_spacing)
        y = bar_base_y - height
        draw.rectangle(
            (x, y, x + bar_width, bar_base_y),
            fill=color
        )
    
    # Save the image
    img.save(output_path)
    print(f"Icon saved to {output_path}")
    return output_path

if __name__ == "__main__":
    # Ensure we're in the assets directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Generate the icon
    generate_signal_booster_icon("icon.png") 