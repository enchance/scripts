#!/bin/bash


# Initialize variables
format="tar.gz"
unique=false
delete=false
dry_run=false
verbose=false
prefix=""
suffix=""
all=false
with_hash=false
full_stop=false

# Function to generate a random 4-character hash
generate_hash() {
    echo $(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 4 | head -n 1)
}

# Function to strip special characters from a string
strip_special_chars() {
    echo "$1" | tr -cd '[:alnum:]_-'
}

# Function to compress a folder
compress_folder() {
    local folder="$1"
    local output_dir="$(dirname "$folder")"
    local base_name=$(basename "$folder")
    local output_name=$(strip_special_chars "${base_name#.}")
    local output_file="${output_dir}/${prefix}${output_name}${suffix}"

    # Check if file already exists and unique option is set
    if [ -e "$output_file.$format" ] && $unique; then
        local hash=$(generate_hash)
        output_file="${output_file}_${hash}"
    fi

    # Append format extension
    output_file="$output_file.$format"

    if $dry_run; then
        echo "Would compress '$folder' to '$output_file'"
        return 0
    fi

    if $verbose; then
        echo "Compressing '$folder' to '$output_file'"
    fi

    case $format in
        zip)     (cd "$output_dir" && zip -r "$(basename "$output_file")" "$base_name") ;;
        rar)     (cd "$output_dir" && rar a "$(basename "$output_file")" "$base_name") ;;
        tar.gz)  tar -czf "$output_file" -C "$output_dir" "$base_name" ;;
        tar.bz2) tar -cjf "$output_file" -C "$output_dir" "$base_name" ;;
        7z)      (cd "$output_dir" && 7z a "$(basename "$output_file")" "$base_name") ;;
        iso)     mkisofs -o "$output_file" "$folder" ;;
        cbz)     (cd "$output_dir" && zip -r "$(basename "$output_file")" "$base_name") ;;
        *)       echo "Unsupported format: $format"; return 1 ;;
    esac

    if [ $? -ne 0 ]; then
        echo "Error compressing '$folder'"
        return 1
    fi

    if $with_hash; then
        (cd "$output_dir" && sha1sum "$(basename "$output_file")" >> sha1-keys)
    fi

    if $delete; then
        if $dry_run; then
            echo "Would delete '$folder'"
        else
            if [ "$PWD" = "$(realpath "$folder")" ]; then
                echo "Warning: Cannot delete '$folder' as it is the current working directory"
            else
                rm -rf "$folder"
            fi
        fi
    fi

    return 0
}

# Parse command-line options
TEMP=$(getopt -o f:udv:p:s:ah --long format:,unique,delete,dry-run,verbose,prefix:,suffix:,all,with-hash,full-stop,help -n "$0" -- "$@")
eval set -- "$TEMP"

while true; do
    case "$1" in
        -f|--format)
            format="$2"; shift 2 ;;
        -u|--unique)
            unique=true; shift ;;
        -d|--delete)
            delete=true; shift ;;
        --dry-run)
            dry_run=true; shift ;;
        -v|--verbose)
            verbose=true; shift ;;
        -p|--prefix)
            prefix="$2"; shift 2 ;;
        -s|--suffix)
            suffix="$2"; shift 2 ;;
        -a|--all)
            all=true; shift ;;
        --with-hash)
            with_hash=true; shift ;;
        --full-stop)
            full_stop=true; shift ;;
        -h|--help)
            print_usage; exit 0 ;;
        --)
            shift; break ;;
        *)
            echo "Internal error!"; exit 1 ;;
    esac
done

# Check if at least one folder is provided
if [ $# -eq 0 ]; then
    echo "Error: No folders specified."
    print_usage
    exit 1
fi

# Process folders
failed_folders=()
for main_folder in "$@"; do
    if [ ! -d "$main_folder" ]; then
        echo "Error: '$main_folder' is not a directory."
        continue
    fi

    shopt -s dotglob  # Enable including hidden files in glob patterns
    for folder in "$main_folder"/*; do
        if [ ! -d "$folder" ]; then
            continue
        fi

        base_name=$(basename "$folder")
        if [ ! "$all" ] && [[ $base_name == .* ]]; then
            echo "Found $base_name"
            continue
        fi

        if [ -z "$(ls -A "$folder")" ]; then
            echo "Warning: '$folder' is empty."
            continue
        fi

        if ! compress_folder "$folder"; then
            failed_folders+=("$folder")
            if $full_stop; then
                echo "Stopping due to error (--full-stop option)"
                break 2
            fi
        fi
    done
    shopt -u dotglob  # Disable including hidden files in glob patterns
done

# Print failed folders
if [ ${#failed_folders[@]} -ne 0 ]; then
    echo "The following folders failed to compress:"
    printf '%s\n' "${failed_folders[@]}"
fi