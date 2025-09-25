#!/usr/bin/env python3

import argparse
from pathlib import Path
import os
import shutil

parser = argparse.ArgumentParser()

parser.add_argument(
    '-s',
    '--source',
    help='Source folder to search images',
    required=True
)

parser.add_argument(
    '-d',
    '--dest',
    help='Destination folder to move images',
    required=True
)

parser.add_argument(
    '-m',
    '--move',
    help='Move files instead of making a copy',
    action='store_true',
)

if __name__ == '__main__':
    args = parser.parse_args()
    
    source = Path(args.source)
    destination = Path(os.path.abspath(args.dest))
    move = args.move

    files_to_move = []

    if not source.exists() or not source.is_dir():
        raise NotADirectoryError('Source folder not found. Make sure that it exists.')

    for dirpath, dirnames, filenames in os.walk(source):
        for filename in filenames:
            if filename.endswith('.jpg'):
                files_to_move.append(Path(os.path.join(dirpath, filename)))

    destination.mkdir(parents=True, exist_ok=True)

    if os.listdir(destination):
        print(f'{destination.as_posix()} contain files. Moving {len(files_to_move)} ? y/n')

        response = input()

        allowed = ['y', 'n']

        while str.lower(response.strip()) not in allowed:
            print('Please type y or n.')
            response = input()

        if response == 'n':
            print('Aborting.')
            exit(0)

    action = shutil.move if move else shutil.copy

    for file in files_to_move:
        action(file, destination)