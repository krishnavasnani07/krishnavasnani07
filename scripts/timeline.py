import os
import re
import math
from datetime import datetime, timedelta

def process_svg(filepath, offset_y=-130, text_offset_y=-15):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove existing timeline if present to allow idempotent runs
    content = re.sub(r'<!-- Custom Inclined Time Timeline -->\s*<g id="time-timeline">.*?</g>\s*</svg>', '</svg>', content, flags=re.DOTALL)
    content = re.sub(r'<g id="time-timeline">.*?</g>\s*</svg>', '</svg>', content, flags=re.DOTALL)

    # 2. Extract cube coordinates
    # Find all translate coordinates in chronological order (first 371 matches represent the calendar grid)
    translates_raw = re.findall(r'transform="translate\((\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\)"', content)
    if len(translates_raw) < 371:
        print(f"Warning: Only found {len(translates_raw)} translations in {os.path.basename(filepath)}. Expected at least 371. Skipping.")
        return

    grid_coords = [(float(x), float(y)) for x, y in translates_raw[:371]]

    # Weeks are groups of 7 days. Week w starts at index 7*w.
    total_weeks = len(grid_coords) // 7
    if total_weeks < 53:
        print(f"Warning: Calculated {total_weeks} weeks in {os.path.basename(filepath)}. Expected 53. Skipping.")
        return

    # Sunday coords of the first and last weeks
    x_start, y_start = grid_coords[0]          # Week 0 Sunday (top-left)
    x_end, y_end = grid_coords[7 * 52]        # Week 52 Sunday (bottom-right)

    # Compute timeline baseline coordinates (offset upwards)
    line_x1 = x_start
    line_y1 = y_start + offset_y
    line_x2 = x_end
    line_y2 = y_end + offset_y

    # Calculate angle of incline
    dx = line_x2 - line_x1
    dy = line_y2 - line_y1
    angle_rad = math.atan2(dy, dx)
    angle_deg = math.degrees(angle_rad)

    # 3. Extract dates from SVG
    # Typical range text format: "YYYY-MM-DD / YYYY-MM-DD"
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})\s*/\s*(\d{4}-\d{2}-\d{2})', content)
    if date_match:
        start_str, end_str = date_match.groups()
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
    else:
        # Fallback if no date range is found
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()

    # 4. Generate monthly transitions and markers
    labels_xml = []
    ticks_xml = []

    # Map each week to its date and gather months
    for w in range(53):
        # Coordinates for this week on the timeline
        fraction = w / 52.0
        w_x = line_x1 + fraction * dx
        w_y = line_y1 + fraction * dy

        # Date for this week
        w_date = start_date + timedelta(weeks=w)

        # Determine if we should render a label for this week
        is_start = (w == 0)
        is_end = (w == 52)
        
        # Month change detection
        month_changed = False
        if w > 0:
            prev_date = start_date + timedelta(weeks=w-1)
            month_changed = (w_date.month != prev_date.month)

        if is_start:
            # Start Marker: ● Month Year (Green)
            label_text = f"● {w_date.strftime('%b %Y')}"
            labels_xml.append(
                f'<text transform="translate({w_x}, {w_y + text_offset_y}) rotate({angle_deg:.2f})" '
                f'font-weight="bold" fill="#4ADE80" text-anchor="middle" font-size="11px">{label_text}</text>'
            )
            # Dot or tick at start
            ticks_xml.append(
                f'<circle cx="{w_x}" cy="{w_y}" r="2.5" fill="#4ADE80" opacity="0.8" />'
            )
        elif is_end:
            # End Marker: ● Month Year (Pink)
            label_text = f"● {w_date.strftime('%b %Y')}"
            labels_xml.append(
                f'<text transform="translate({w_x}, {w_y + text_offset_y}) rotate({angle_deg:.2f})" '
                f'font-weight="bold" fill="#ff79c6" text-anchor="middle" font-size="11px">{label_text}</text>'
            )
            # Dot or tick at end
            ticks_xml.append(
                f'<circle cx="{w_x}" cy="{w_y}" r="2.5" fill="#ff79c6" opacity="0.8" />'
            )
        elif month_changed:
            # Normal month transition
            # Format year suffix if it's January (e.g. Jan '26)
            if w_date.month == 1:
                label_text = w_date.strftime("%b '%y")
            else:
                label_text = w_date.strftime("%b")
                
            labels_xml.append(
                f'<text transform="translate({w_x}, {w_y + text_offset_y}) rotate({angle_deg:.2f})" '
                f'fill="#8b949e" text-anchor="middle" font-size="11px">{label_text}</text>'
            )
            # Draw tick mark perpendicular to the incline line
            # Perpendicular angle = angle + pi/2
            perp_dx = -math.sin(angle_rad) * 6
            perp_dy = math.cos(angle_rad) * 6
            ticks_xml.append(
                f'<line x1="{w_x}" y1="{w_y}" x2="{w_x - perp_dx}" y2="{w_y - perp_dy}" '
                f'stroke="#4ADE80" stroke-width="1.2" opacity="0.6" />'
            )

    # 5. Compute Arrowhead coordinates
    # Arrowhead length 10, half-width 4
    arrow_len = 10
    arrow_width = 4
    
    # Back center of the arrowhead
    back_x = line_x2 - arrow_len * math.cos(angle_rad)
    back_y = line_y2 - arrow_len * math.sin(angle_rad)
    
    # Perpendicular vector components for width
    perp_x = -math.sin(angle_rad) * arrow_width
    perp_y = math.cos(angle_rad) * arrow_width
    
    # Left and right corner coordinates
    left_x = back_x - perp_x
    left_y = back_y - perp_y
    right_x = back_x + perp_x
    right_y = back_y + perp_y

    arrow_points = f"{line_x2:.2f},{line_y2:.2f} {left_x:.2f},{left_y:.2f} {right_x:.2f},{right_y:.2f}"

    # Assemble SVGs
    timeline_group = f"""<!-- Custom Inclined Time Timeline -->
  <g id="time-timeline" style="font-family: 'Fira Code', Consolas, Monaco, monospace;">
    <!-- Subtle glowing cyber line -->
    <line x1="{line_x1:.2f}" y1="{line_y1:.2f}" x2="{line_x2:.2f}" y2="{line_y2:.2f}" stroke="#4ADE80" stroke-width="2" opacity="0.45" />
    <!-- Direction Arrowhead -->
    <polygon points="{arrow_points}" fill="#4ADE80" opacity="0.45" />
    
    <!-- Month Tick Marks -->
    {''.join(ticks_xml)}
    
    <!-- Timeline Labels -->
    {''.join(labels_xml)}
  </g>
</svg>"""

    # Inject the group right before the closing tag
    new_content = content.replace("</svg>", timeline_group)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Successfully processed timeline for {os.path.basename(filepath)}")

def process_all_svgs():
    directory = "profile-3d-contrib"
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    for filename in os.listdir(directory):
        if filename.endswith(".svg"):
            filepath = os.path.join(directory, filename)
            process_svg(filepath)

if __name__ == "__main__":
    process_all_svgs()
