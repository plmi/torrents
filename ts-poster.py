#!/usr/bin/env python3

from enum import Enum, StrEnum
import json
import logging
import os
import re
import sys
import argparse
import traceback
import requests


def get_imdbid(nfo_path: str) -> str:
    with open(nfo_path, 'r') as f:
        content: str = f.read()
        match = re.search(r'tt\d{7,8}', content)
        if match:
            return match.group()
    raise ValueError(f'Could not find imdb id in file {nfo_path}')


class Category(Enum):
    MOVIE_2160 = 42
    MOVIE_1080 = 9


class ReleaseType(StrEnum):
    P2P = 'p2p'
    SCENE = 'scene'


def get_category(dirname: str) -> Category:
    if '2160p' or  'COMPLETE.UHD.BLURAY' in dirname:
        return Category.MOVIE_2160
    if '1080p' or 'COMPLETE.BLURAY' in dirname:
        return Category.MOVIE_1080
    raise ValueError(f'Unknown category: {dirname}')


def is_string_in_file(file_path: str, value: str) -> bool:
    if not os.path.isfile(file_path):
        return False
    with open(file_path, 'r') as file:
        for line in file:
            if value in line:
                return True
    logging.debug(f'Could not find {value} in {file_path}')
    return False


def append_new_line(file_path: str, line) -> None:
    with open(file_path, 'a+') as file:
        file.write(line + '\n')

def get_group(dirname: str) -> str:
    return dirname.split('-')[-1]


def get_release_type(group: str) -> ReleaseType:
    if is_string_in_file('p2p.txt', group):
        return ReleaseType.P2P
    elif is_string_in_file('scene.txt', group):
        return ReleaseType.SCENE
    type: str = input(f'Select release type for {group} [p2p|scene]: ')
    if type not in ['p2p', 'scene']:
        raise ValueError(f'Unknown user input: {type}')
    file_path: str = 'p2p.txt' if type == 'p2p' else 'scene.txt'
    append_new_line(file_path, group)
    get_release_type(group)


def get_mediainfo(filename: str) -> str:
    return json.loads(read_file(filename))


def read_file(filename: str) -> str:
    if not os.path.isfile(filename):
        raise ValueError(f'File not found: {filename}')
    with open(filename, 'r') as f:
        return f.read()


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='upload torrent')
    parser.add_argument('-t', '--torrent', type=str, help='path to torrent file')
    parser.add_argument('-n', '--nfo', type=str, help='path to nfo file')
    parser.add_argument('-m', '--mediainfo', type=str, help='path to media info json')
    parser.add_argument('-d', '--dirname', type=str, help='dirname')
    parser.add_argument('-k', '--key', type=str, help='api key')
    args = parser.parse_args()

    files: dict = {
        'torrent': open(args.torrent, 'rb'),
        'nfo': open(args.nfo, 'rb'),
    }
    group: str = get_group(args.dirname)
    payload: dict = {
        'name': args.dirname,
        'category': get_category(args.dirname),
        'mediainfo': get_mediainfo(args.mediainfo),
        'imdbid': get_imdbid(args.nfo),
        'anonymous': 'true',
        'nfo': open(args.nfo, 'rb'),
        'release_type': get_release_type(group),
    }
    headers: dict = {
        'User-Agent': 'tsyn/v0.6.0'
    }

    url: str = f'https://torrent-syndikat.org/{args.key}/v1/upload.php'
    response: requests.Response = requests.post(url, files=files, data=payload, timeout=5, headers=headers)
    if response.status_code == 200:
        logging.info(f'Upload of {args.dirname} successful')
        print(response.content)
    else:
        logging.error(f'Request failed with status code {response.status_code}')
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        main()
    except Exception as e:
        logging.error(str(e))
        traceback.print_exc(file=sys.stdout)
