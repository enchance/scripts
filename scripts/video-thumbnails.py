#!/usr/bin/env python3

import os, sys, click, shutil
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips
from urllib.parse import quote, urlparse
from icecream import IceCreamDebugger

from utils.utils import command_config, path_config, group_config, clean_filename


# html_filename = 'thumbnails.html'
# thumb_folder = '.thumbnails'
__version__ = '0.2.0'
ic = IceCreamDebugger(prefix='')
PROGRAM_NAME = 'HTML Thumbnail Generator'
VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mkv', '.mov', '.webm')


total_created = 0
total_moved = 0
createlist = []
errors = {}


def create_thumbnail(video_path, output_folder):
    global total_created

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

    total_created += 1
    return thumbnail_path, total_duration


def generate_html_head(label: str) -> str:
    html = """
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
        <h1>%s</h1>
        <ul>
    """ % label
    return html


def generate_html_tile(tail: str, url_friendly_path: str, thumbnail_path: str, video_name: str,
                          formatted_duration: str) -> str:
    html = f"""
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
            """
    return html


def generate_html_footer() -> str:
    html = """
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
    return html


def create_html(thumbnail_folder: Path, videos_folder: Path, html_name: str, label: str):
    html_content = generate_html_head(label)

    for file_name in sorted(os.listdir(thumbnail_folder)):
        name_only, ext = os.path.splitext(file_name)

        if name_only[0:-10] not in createlist:
            continue

        if file_name.endswith('_thumbnail.webm'):
            thumbnail_path = os.path.join(thumbnail_folder, file_name)
            video_name = os.path.splitext(file_name)[0].replace('_thumbnail', '')
            video_path = os.path.join(videos_folder, video_name + '.mp4')
            url_friendly_path = quote(urlparse(video_path).path)
            _, ext = os.path.split(video_path)

            _, full_video_duration = create_thumbnail(video_path, thumbnail_folder)
            formatted_duration = f"{int(full_video_duration) // 3600:02d}:{int((full_video_duration % 3600) // 60):02d}:{int(full_video_duration % 60):02d}"

            html_content += generate_html_tile(ext, url_friendly_path, thumbnail_path, video_name, formatted_duration)

    html_content += generate_html_footer()

    with open(html_name, 'w') as html_file:
        html_file.write(html_content)


def remove_temp_files():
    temp_files = ['temp_thumbnail_1.mp4', 'temp_thumbnail_2.mp4', 'temp_thumbnail_3.mp4']
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def generate_thumbnail_folder(path: Path, name: str) -> Path:   # noqa
    thumb_path = Path(os.path.join(path, name))
    os.makedirs(thumb_path, exist_ok=True)
    return thumb_path


def create_thumbnails(folder_path: Path, thumbnail: str, html: str, title: str, show_message: bool = True):
    thumbnail_path = generate_thumbnail_folder(folder_path, thumbnail)

    # Rename
    files = [i for i in os.listdir(folder_path) if os.path.isfile(i)]
    for name in files:
        clean_filename(folder_path, name)

    dirnames = sorted(os.listdir(folder_path))
    for file_name in dirnames:
        if file_name.lower().endswith(VIDEO_EXTENSIONS):
            video_path = os.path.join(folder_path, file_name)

            try:
                thumbnail_pat, _ = create_thumbnail(video_path, thumbnail_path)
            except Exception:
                continue

            name, ext = os.path.splitext(file_name)
            createlist.append(name)

    create_html(thumbnail_path, folder_path, f'{html}.html', title)
    remove_temp_files()

    if show_message:
        print(f'[COMPLETE]: {total_created} thumbnails generated')


# @cli.command(**command_config)
# @click.argument('input_path', type=path_config)
# @click.argument('video_names')

def move_completed(input_path: Path, video_names: str, folder_name: str):    # noqa
    """
    Move watched movies to the DONE folder. File names must be separated by a "::" creating one long string.
    The complete list of watched videos can be copied from the browser console.
    """
    global total_moved
    destination_path = os.path.join(input_path, folder_name)
    dataset = set(video_names.split('::'))

    ll = []
    for file_name in os.listdir(input_path):
        if file_name.lower().endswith(VIDEO_EXTENSIONS):
            if file_name in dataset:
                ll.append(file_name)

    if ll:
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        for name in ll:
            try:
                from_path = os.path.join(input_path, name)
                to_path = os.path.join(destination_path, name)
                shutil.move(from_path, to_path)
                total_moved += 1
                print(f'[MOVED]: {name}')
            except Exception as _:
                pass

    print(f'[COMPLETE]: {total_moved} files moved')


@click.command(**command_config)
@click.version_option(__version__, prog_name=PROGRAM_NAME)
@click.argument('input_path', type=path_config)
@click.argument('video_names', default=None, required=False)
@click.option('--thumbnail', '-t', help='Name of thumbnail folder', default='.thumbnails', show_default=True)
@click.option('--html', '-h', help='Name of HTML file', default='thumbnails', show_default=True)
@click.option('--label', '-l', help='Title of the generated HTML file', default='Thumbnails', show_default=True)
@click.option('--done', '-d', help='Folder name to move watched videos to', default='__done', show_default=True)
@click.option('--regenerate', '-r', help='Regenerate the HTML file after moving files', is_flag=True, default=True,
              show_default=True)
def main(input_path: Path, thumbnail: str, html: str, label: str, video_names: str | None, done: str, regenerate: bool):
    """
    Generate thumbnails of video files and create an html file so they can be viewed. Uses your browser's default
    player to watch the videos.\n

    To move all watched videos to your "done" folder paste the string of filenames located in the console in
    VIDEO_NAMES. Make sure the
    string is quoted to prevent errors.
    """
    if video_names is None:
        return create_thumbnails(input_path, thumbnail, html, label)

    move_completed(input_path, video_names, done)
    if regenerate:
        create_thumbnails(input_path, thumbnail, html, label, show_message=False)
        print(f'[COMPLETE]: HTML file updated')


if __name__ == "__main__":
    main()
