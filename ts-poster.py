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
    if '2160p' or 'COMPLETE.UHD.BLURAY' in dirname:
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
    return get_release_type(group)


def get_mediainfo(filename: str) -> str:
    return read_file(filename)


def read_file(filename: str) -> str:
    if not os.path.isfile(filename):
        raise ValueError(f'File not found: {filename}')
    with open(filename, 'r') as f:
        return f.read()


def get_csrf_token(session: requests.Session) -> str | None:
    response: requests.Response = session.get('https://torrent-syndikat.org/eing.php')
    if response.status_code != 200:
        logging.error(f'Request failed: {response.status_code}')
        sys.exit(1)

    match = re.search(f"value='([a-z0-9]+)'", response.text)
    if match:
        return match.group(1)
    return None


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description='upload torrent')
    parser.add_argument('-t', '--torrent', type=str, help='path to torrent file')
    parser.add_argument('-n', '--nfo', type=str, help='path to nfo file')
    parser.add_argument('-m', '--mediainfo', type=str, help='path to media info json')
    parser.add_argument('-d', '--dirname', type=str, help='dirname')
    parser.add_argument('-k', '--key', type=str, help='api key')
    parser.add_argument('-u', '--username', type=str, help='username')
    parser.add_argument('-p', '--password', type=str, help='password')
    parser.add_argument('--proxy', action=argparse.BooleanOptionalAction, default=False, help='use proxy http://127.0.0.1:8080 to debug')
    args = parser.parse_args()

    proxies: dict = {}
    if args.proxy:
        proxies = { 'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080' }


    with requests.Session() as session:
        csrf_token: str | None = get_csrf_token(session)
        print(csrf_token)
        if not csrf_token:
            logging.error('Could not extract csrf token')
            sys.exit(1)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'tst': csrf_token,
            'username': args.username,
            'password': args.password,
        }
        response: requests.Response = session.post('https://torrent-syndikat.org/eing2.php', data=payload, headers=headers, proxies=proxies, verify=False, allow_redirects=True)
        if response.status_code != 200:
            logging.error(f'Login failed with status code: {response.status_code}')
            sys.exit(1)

        files: dict = {
            'torrent': (args.torrent, open(args.torrent, 'rb'), 'application/x-bittorrent'),
            'nfo': (args.nfo, open(args.nfo, 'r'), 'text/x-nfo'),
        }
        group: str = get_group(args.dirname)
        payload: dict = {
            'MAX_FILE_SIZE': '3145728',
            'category': get_category(args.dirname).value,
            'release_type': get_release_type(group),
            'name': args.dirname,
            'mediainfo': get_mediainfo(args.mediainfo),
            'imdbid': get_imdbid(args.nfo),
            'posterlink': '',
            'description': '',
            'anonymous': 'yes',
            'genres': 'yes',
            'pid': '',
        }
        headers: dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.57 Safari/537.36'
        }

        url: str = 'https://torrent-syndikat.org/tsystem/uppit.php'
        response: requests.Response = session.post(url, files=files, data=payload, timeout=5, headers=headers, proxies=proxies, verify=False, allow_redirects=True)
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
