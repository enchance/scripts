#!/usr/bin/env python3


import os, sys, re
from moviepy.editor import VideoFileClip, concatenate_videoclips
from urllib.parse import quote, urlparse
from pathvalidate import sanitize_filename


html_filename = 'thumbnails.html'
thumb_folder = '.thumbnails'
total = 0
createlist = []
errors = {}


# def sanitize_filename(filename):
#   """
#   Sanitizes a filename by removing all special characters except letters, numbers, periods, and dashes.
#   """
#   valid_chars = r"[a-zA-Z0-9_\-\.]+"
#   return re.sub(r"[^\w\-\.\s]", "", filename)


def create_thumbnail(video_path, output_folder):
    global total

    # Check if thumbnail already exists
    thumbnail_name = os.path.splitext(os.path.basename(video_path))[0] + '_thumbnail.webm'
    thumbnail_path = os.path.join(output_folder, thumbnail_name)
    
    total_duration = VideoFileClip(video_path).duration

    if os.path.exists(thumbnail_path):
        # print(f'[SKIP]: {os.path.basename(video_path)}: {thumbnail_path}')
        return None, total_duration

    # Calculate time intervals
    interval_1_start = total_duration * 0.1
    interval_1_end = min(interval_1_start + 5, total_duration)
    interval_2_start = total_duration * 0.4
    interval_2_end = min(interval_2_start + 10, total_duration)
    interval_3_start = total_duration * 0.8
    interval_3_end = min(interval_3_start + 10, total_duration)

    # Extract clips from specified time intervals
    clip_1 = VideoFileClip(video_path).subclip(interval_1_start, interval_1_end)
    clip_2 = VideoFileClip(video_path).subclip(interval_2_start, interval_2_end)
    clip_3 = VideoFileClip(video_path).subclip(interval_3_start, interval_3_end)

    try:
        # Concatenate the clips into a single thumbnail
        thumbnail = concatenate_videoclips([clip_1, clip_2, clip_3], method="compose").resize(height=150)
    except Exception as e:
        print(e)
        raise

    # Save the thumbnail as a WebM file
    thumbnail_name = os.path.splitext(os.path.basename(video_path))[0] + '_thumbnail.webm'
    thumbnail_path = os.path.join(output_folder, thumbnail_name)
    thumbnail.without_audio().write_videofile(thumbnail_path, codec="libvpx", bitrate="200k", fps=12)

    # Rename the original video file without special characters
    sanitized_video_name = os.path.splitext(os.path.basename(video_path))[0] + '.mp4'
    sanitized_video_path = os.path.join(os.path.dirname(video_path), sanitized_video_name)
    os.rename(video_path, sanitized_video_path)

    total += 1
    return thumbnail_path, total_duration


def create_html(thumbnail_folder, videos_folder):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            html, body {font-family:arial, sans-serif; background:#444; color:#DDD;}
            ul {list-style:none; padding:0; display:flex; flex-wrap:wrap;}
            li {padding:10px; width:300px;}
            li:hover {background:slateblue;}
            li > div {width:300px; background:#000; margin-bottom:5px; padding:12px 0 8px;}
            li footer {display:flex; justify-content:space-between;}
            video {width:300px; height:150px; cursor:pointer;}
            h1 {margin-left:10px; color:#DDD;}
            h6 {font-size:0.95rem; margin:0; line-height:1.2rem;}
            .done {background:#999; color:#000;}
            .done:hover {background:#BBB!important;}
            .duration {margin-left:10px;}
        </style>
        <title>Video Thumbnails</title>
    </head>
    <body>
        <h1>Thumbnails</h1>
        <ul>
    """
    for file_name in sorted(os.listdir(thumbnail_folder)):
        name_only, ext = os.path.splitext(file_name)

        if name_only[0:-10] not in createlist:
            continue

        if file_name.endswith('_thumbnail.webm'):
            thumbnail_path = os.path.join(thumbnail_folder, file_name)
            video_name = os.path.splitext(file_name)[0].replace('_thumbnail', '')
            video_path = os.path.join(videos_folder, video_name + '.mp4')
            url_friendly_path = quote(urlparse(video_path).path)
            head, tail = os.path.split(video_path)

            _, full_video_duration = create_thumbnail(video_path, thumbnail_folder)
            formatted_duration = f"{int(full_video_duration) // 3600:02d}:{int((full_video_duration % 3600) // 60):02d}:{int(full_video_duration % 60):02d}"

            html_content += f'''
            <li onclick="this.classList.add(\'done\');mark(\'{tail}\', \'{url_friendly_path}\')">
                <div>
                    <video loop muted onmouseover="this.play()" onmouseout="this.pause()">
                        <source src="{thumbnail_path}" type="video/webm">
                    </video>
                </div>
                <footer>
                    <h6>{video_name}</h6>
                    <div class="duration">{formatted_duration}</div>
                </footer>
            </li>
            '''

    html_content += """
        </ul>
        <script>
            let watched = [];
            function mark(tail, path) {
                watched.push(tail)
                console.log(watched.join('::'))
                window.open(path, '_blank')
            }
        </script>
    </body>
    </html>
    """

    with open(html_filename, 'w') as html_file:
        html_file.write(html_content)


def rename_file(path: str, file: str) -> str | None:
    try:
        new_file = sanitize_filename(file)
        new_path = os.path.join(path, new_file)
        fullpath = os.path.join(path, file)
        if new_file != file:
            os.rename(fullpath, new_path)
        return new_file
    except Exception:       # noqa
        errors.setdefault('filenames', [])
        errors['filenames'].append(file)
        return None


def remove_temp_files():
    temp_files = ['temp_thumbnail_1.mp4', 'temp_thumbnail_2.mp4', 'temp_thumbnail_3.mp4']
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_folder>")
        sys.exit(1)

    folder_path = os.path.abspath(sys.argv[1])

    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        sys.exit(1)

    thumbnails_folder = os.path.join(folder_path, thumb_folder)
    os.makedirs(thumbnails_folder, exist_ok=True)

    # Rename
    files = [i for i in os.listdir(folder_path) if os.path.isfile(i)]
    for name in files:
        rename_file(folder_path, name)

    # dirnames = os.listdir(folder_path)
    # for file_name in dirnames:
    #     filepath = os.path.join(folder_path, file_name)
    #     if os.path.isfile(filepath):
    #         new_filename = sanitize_filename(file_name)
    #         if new_filename != file_name:
    #             os.rename(filepath, os.path.join(folder_path, new_filename))

    dirnames = sorted(os.listdir(folder_path))
    for file_name in dirnames:
        if file_name.lower().endswith(('.mp4', '.avi', '.mkv', '.mov')):
            video_path = os.path.join(folder_path, file_name)
            
            try:
                thumbnail_pat, _ = create_thumbnail(video_path, thumbnails_folder)
            except Exception:
                continue

            name, ext = os.path.splitext(file_name)
            createlist.append(name)

    create_html(thumbnails_folder, folder_path)
    remove_temp_files()
    print(f'[COMPLETE]: {total} thumbnails generated.')
