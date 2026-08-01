import os

def postprocess_svgs():
    directory = "profile-3d-contrib"
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    timeline_group = """
  <!-- Custom Inclined Time Timeline -->
  <g id="time-timeline" style="font-family: 'Fira Code', Consolas, Monaco, monospace; font-size: 13px;">
    <!-- Dashed guideline parallel to the grid -->
    <line x1="80" y1="210" x2="1140" y2="820" stroke="#30363d" stroke-width="1.5" stroke-dasharray="4 4" />
    
    <!-- Inclined Text Labels -->
    <text transform="translate(80, 200) rotate(29.9)" font-weight="bold" fill="#5af78e">◀ Jul 2025 (Start)</text>
    <text transform="translate(560, 475) rotate(29.9)" fill="#8b949e">Flow of Time ──▶</text>
    <text transform="translate(1000, 725) rotate(29.9)" font-weight="bold" fill="#ff79c6">Aug 2026 (End) ▶</text>
  </g>
</svg>"""

    for filename in os.listdir(directory):
        if filename.endswith(".svg"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if 'id="time-timeline"' in content:
                print(f"Timeline already present in {filename}, skipping.")
                continue

            if "</svg>" in content:
                new_content = content.replace("</svg>", timeline_group)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Successfully injected inclined timeline into {filename}")
            else:
                print(f"Could not find </svg> tag in {filename}")

if __name__ == "__main__":
    postprocess_svgs()
