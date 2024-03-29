import click, os, re        # noqa
from click_help_colors import HelpColorsCommand, HelpColorsGroup
from pathlib import Path
from pathvalidate import sanitize_filename


command_config = dict(cls=HelpColorsCommand, help_options_color='green', help_headers_color='blue')
group_config = dict(cls=HelpColorsGroup, help_options_color='green', help_headers_color='blue')
path_config = click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, path_type=Path, resolve_path=True)


def clean_filename(path: Path, filename: str) -> str:
    new_file = re.sub(r"[^\w\-.\s]", '', sanitize_filename(filename))
    new_path = os.path.join(path, new_file)
    fullpath = os.path.join(path, filename)
    if new_file != filename:
        os.rename(fullpath, new_path)
    return new_file