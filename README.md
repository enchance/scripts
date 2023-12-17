System Scripts
===================

Useful Python and BASH CLI scripts for my personal use.

Install
----------------
Install necessary dependencies

```bash
pip install typer[all] Pillow==10.1.0 moviepy
```


Python
--------------

All scripts have their own `--help` option for finding out how they're used.

- `chunk.py`: Chunk files into subfolders in the form of `chunk-n`. Useful for organizing a folder full of images. 
  Works on any file not just images.
- `merge.py`: Collates all files from folders using a specific prefix (e.g. "chunk"). The 
  opposite of using the `chunk.py` script.


BASH
-------------

To follow