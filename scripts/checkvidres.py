#!/usr/bin/env python3

import subprocess
import json
import sys

def get_video_resolution(file_path):
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'json',
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"ffprobe error: {result.stderr}")

    info = json.loads(result.stdout)
    width = info['streams'][0]['width']
    height = info['streams'][0]['height']
    return width, height

if len(sys.argv) != 2:
    print("Usage: python check_resolution.py <path_to_video_file>")
    sys.exit(1)

video_file = sys.argv[1]

try:
    width, height = get_video_resolution(video_file)
    print(f"Resolution: {width}x{height}")

    if height == 1080:
        print("The video is 1080p")
    elif height == 1440:
        print("The video is 1440p")
    elif height == 2160:
        print("The video is 4K")
    elif height == 2048:
        print("The video is 2K")
    else:
        print(f"The video is {height}p")
except Exception as e:
    print(f"Error: {e}")
