#!/usr/bin/env python3

# """Copy figures used by document."""
import os
import shutil
import sys


DEP_FILE = sys.argv[1]
TARGET_DIR = sys.argv[2]
EXTENSIONS = ['pdf', 'pdf_tex', 'png', 'jpg', 'jpeg', 'bbl', 'bib', 'tex']

print("Extracting all dependencies of ", DEP_FILE, " and copying them in ", TARGET_DIR)

if not os.path.isfile(DEP_FILE):
    print(".dep file ", DEP_FILE, " does not exist, make sure you have \RequirePackage{snapshot} at the beginning of your latex file")

if not os.path.exists(TARGET_DIR):
    os.makedirs(TARGET_DIR)


def copy_image_files():
    with open(DEP_FILE, 'r') as f:
        for line in f:
            if '*{file}' not in line:
                continue
            value = line.split('{')[2].split('}')
            source = value[0]
            _, e = os.path.splitext(source)
            e = e.lower()[1:]
            if e not in EXTENSIONS:
                continue
            print(source)
            try:
                shutil.copy(source, TARGET_DIR)
            except:
                print(source, " can't be copied")

if __name__ == '__main__':
    copy_image_files()