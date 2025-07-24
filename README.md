# GIMP DDS Export Plugin (texconv)

A GIMP 3.0 plugin to export images as DDS files using the external tool [`texconv`](https://github.com/microsoft/DirectXTex).  
This plugin provides a simple dialog to choose DDS compression format, mipmaps generation, sRGB colorspace, and overwrite options.

---

## Features

- Export GIMP images to DDS format without relying on built-in DDS support.
- Supports popular DDS compression formats (BC1–BC7) and uncompressed RGBA.
- Optionally generate mipmaps.
- Optionally mark the texture as sRGB (perceptual color space).
- Option to overwrite existing DDS files.
- Uses `texconv.exe` as the external converter tool (Windows only).

---

## Requirements

- GIMP 3.0 or newer.
- Python 3 with GObject Introspection bindings.
- [`texconv`](https://github.com/microsoft/DirectXTex) executable available on your system.
- Windows OS (due to `texconv.exe` and specific subprocess flags).

---

## Installation

1. Place the plugin script (e.g. `dds_export_texconv.py`) in your GIMP plug-ins folder:

   - Windows: `%APPDATA%\GIMP\3.0\plug-ins\`
   - Linux: `~/.config/GIMP/3.0/plug-ins/`

2. Make sure the script is executable (Linux/macOS):

   ```bash
   chmod +x dds_export_texconv.py
