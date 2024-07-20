#!/bin/bash

# Check if the folder is specified
if [ -z "$1" ]; then
  echo "Usage: $0 <folder>"
  exit 1
fi

# Check if the specified folder exists
if [ ! -d "$1" ]; then
  echo "Error: Directory $1 does not exist."
  exit 1
fi

# Define the folder and output file
folder="$1"
output_file="sha256-keys"
file_count=0

# Clear the output file if it exists
> "$output_file"

# Loop through each file in the specified folder
for file in "$folder"/*; do
  echo $file
  # Check if it's a file (not a directory) and not the output file
  if [ -f "$file" ] && [ "$(basename "$file")" != "$output_file" ]; then
    # Compute the SHA256 hash and append to the output file
    sha256sum "$file" >> "$output_file"
    ((file_count++))
  fi
done

echo "$file_count files hashed and saved to $output_file."
