import os
import re

def process_svg(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove existing timeline if present
    content = re.sub(r'<!-- Custom Inclined Time Timeline -->\s*<g id="time-timeline">.*?</g>\s*</svg>', '</svg>', content, flags=re.DOTALL)
    content = re.sub(r'<g id="time-timeline">.*?</g>\s*</svg>', '</svg>', content, flags=re.DOTALL)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully cleaned timeline for {os.path.basename(filepath)}")

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
