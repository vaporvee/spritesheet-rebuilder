import os
import json
import argparse
from PIL import Image
from collections import deque

def load_config_from_file(config_path):
    if not os.path.isfile(config_path):
        print(f"⚠️  Config file '{config_path}' not found.")
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)

def parse_args():
    parser = argparse.ArgumentParser(description="Spritesheet frame extractor + rebuilder")
    parser.add_argument("--config", type=str, default=None, help="Optional path to JSON config file")
    parser.add_argument("--input-folder", type=str, help="Folder with input images")
    parser.add_argument("--output-folder", type=str, help="Target folder for new spritemaps")
    parser.add_argument("--scale", type=float, help="Scaling factor for individual frames")
    parser.add_argument("--padding", type=int, help="Pixel spacing between frames in the new spritemap")
    parser.add_argument("--columns", type=int, help="Number of columns in the new spritemap")
    parser.add_argument("--rows", type=int, help="Number of rows in the new spritemap")
    parser.add_argument("--sort", action="store_true", help="Sort frames by position in original image")
    parser.add_argument("--frame-repeat", type=int, help="Number of times to repeat each frame in the output")
    return parser.parse_args()

def merge_config(args, file_config):
    config = {
        "input_folder": "./spritesheets",
        "output_folder": "processed",
        "scale_factor": 1,
        "target_padding": 1,
        "output_columns": None,
        "output_rows": None,
        "sort_by_position": True,
        "frame_repeat": 1,
    }
    config.update(file_config)
    if args.input_folder: config["input_folder"] = args.input_folder
    if args.output_folder: config["output_folder"] = args.output_folder
    if args.scale is not None: config["scale_factor"] = args.scale
    if args.padding is not None: config["target_padding"] = args.padding
    if args.columns is not None: config["output_columns"] = args.columns
    if args.rows is not None: config["output_rows"] = args.rows
    if args.sort: config["sort_by_position"] = True
    if args.frame_repeat is not None: config["frame_repeat"] = args.frame_repeat
    return config

def get_connected_regions(img):
    width, height = img.size
    pixels = img.load()
    visited = [[False] * height for _ in range(width)]
    regions = []
    def is_valid(x, y):
        return 0 <= x < width and 0 <= y < height
    def is_nontransparent(x, y):
        return pixels[x, y][3] != 0
    for y in range(height):
        for x in range(width):
            if not visited[x][y] and is_nontransparent(x, y):
                q = deque()
                q.append((x, y))
                visited[x][y] = True
                xmin, xmax, ymin, ymax = x, x, y, y
                while q:
                    cx, cy = q.popleft()
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = cx + dx, cy + dy
                            if (dx != 0 or dy != 0) and is_valid(nx, ny):
                                if not visited[nx][ny] and is_nontransparent(nx, ny):
                                    visited[nx][ny] = True
                                    q.append((nx, ny))
                                    xmin = min(xmin, nx)
                                    xmax = max(xmax, nx)
                                    ymin = min(ymin, ny)
                                    ymax = max(ymax, ny)
                regions.append((xmin, ymin, xmax + 1, ymax + 1))
    return regions

def pad_frame_to_size(frame, target_size):
    target_w, target_h = target_size
    w, h = frame.size
    new_img = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    x = (target_w - w) // 2
    y = (target_h - h) // 2
    new_img.paste(frame, (x, y))
    return new_img

def crop_and_process(img, regions, config):
    frames = [img.crop(box) for box in regions]
    if config["scale_factor"] != 1:
        scaled_frames = []
        for frame in frames:
            w, h = frame.size
            new_size = (int(w * config["scale_factor"]), int(h * config["scale_factor"]))
            scaled_frames.append(frame.resize(new_size, Image.NEAREST))
        frames = scaled_frames
    if config["sort_by_position"]:
        regions, frames = zip(*sorted(zip(regions, frames), key=lambda pair: (pair[0][1], pair[0][0])))
    max_w = max(f.width for f in frames)
    max_h = max(f.height for f in frames)
    frames = [pad_frame_to_size(f, (max_w, max_h)) for f in frames]
    repeated_frames = []
    for frame in frames:
        repeated_frames.extend([frame] * config["frame_repeat"])
    frames = repeated_frames
    total = len(frames)
    cols = config["output_columns"] or int(total**0.5)
    rows = config["output_rows"] or ((total + cols - 1) // cols)
    new_w = cols * (max_w + config["target_padding"]) - config["target_padding"]
    new_h = rows * (max_h + config["target_padding"]) - config["target_padding"]
    new_img = Image.new("RGBA", (new_w, new_h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        col = i % cols
        row = i // cols
        x = col * (max_w + config["target_padding"])
        y = row * (max_h + config["target_padding"])
        new_img.paste(frame, (x, y))
    return new_img

def process_spritesheet(filepath, config):
    img = Image.open(filepath).convert("RGBA")
    regions = get_connected_regions(img)
    print(f"{os.path.basename(filepath)}: {len(regions)} frames recognized")
    new_img = crop_and_process(img, regions, config)
    os.makedirs(config["output_folder"], exist_ok=True)
    filename = os.path.basename(filepath)
    output_path = os.path.join(config["output_folder"], filename)
    new_img.save(output_path)
    print(f"✅ Saved: {output_path}")

def main():
    args = parse_args()
    config_path = args.config if args.config else "config.json"
    file_config = load_config_from_file(config_path) if os.path.isfile(config_path) else {}
    config = merge_config(args, file_config)
    print(f"\n📁 Input: {config['input_folder']} → 📁 Output: {config['output_folder']}\n")
    for root, _, files in os.walk(config["input_folder"]):
        for filename in files:
            if filename.lower().endswith(".png"):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, config["input_folder"])
                output_path = os.path.join(config["output_folder"], os.path.dirname(relative_path))
                os.makedirs(output_path, exist_ok=True)
                file_config = config.copy()
                file_config["output_folder"] = output_path
                process_spritesheet(filepath, file_config)

main()
