# Spritesheet Frame Rebuilder

Fix individual frames from spritesheet PNG images by detecting connected non-transparent regions and rebuild new spritesheets with options for scaling, padding, layout, and frame repetition.

---

## Features

- Automatically detects connected non-transparent regions as frames
- Supports scaling individual frames
- Pads frames to uniform size
- Sorts frames by their position in the original image (optional)
- Customizable output grid layout (columns & rows)
- Repeat frames multiple times for animation or sprite reuse
- Configurable via JSON config file and/or CLI arguments (`--help` for more info)

---

## Installation

Requires [Python 3.7+](https://www.python.org/downloads/) and [Pillow](https://pypi.org/project/pillow/):

```bash
pip install Pillow
```
## Credits
#### [@koyu](https://github.com/koyuawsmbrtn):
 - Original script
