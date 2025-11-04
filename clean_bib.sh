#!/bin/bash

# Check if the user provided a filename
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 filename.bib"
  exit 1
fi

# Define the input file
input_file="$1"

# Use sed to delete lines containing 'doi =', 'url =', or 'issn ='
sed '/^\s*doi\s*=.*/d;/^\s*url\s*=.*/d;/^\s*issn\s*=.*/d' "$input_file" > cleaned_"$input_file"

echo "Cleaned file created: cleaned_$input_file"