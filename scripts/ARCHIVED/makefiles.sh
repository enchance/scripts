#!/bin/bash
# Script to create empty files in the specified folder.
if [ -z "$1" ]; then
	echo "Enter the destination folder as a parameter."
	exit
elif [ ! -d "$1" ]; then
	echo "No such folder."
	exit
fi

# Change folder and discard output and errors
cd $1 1> /dev/null 2>&1
read -p "Enter the no. of empty files: " fileno
echo "Creating empty files..."
for ((i=1; i<=fileno; i++))
do
	touch file-$i
done