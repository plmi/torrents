#!/usr/bin/env python3

import os
import re
import sys
import json
import logging
import argparse
import requests


class NfoDetails:
      def __init__(self, dirname: str, nfo_name: str, nfo_url: str):
        self.__dirname: str = dirname
        self.__nfo_name: str = nfo_name
        self.__nfo_url: str = nfo_url

      @property
      def dirname(self) -> str:
        return self.__dirname
      
      @property
      def nfo_name(self) -> str:
        return self.__nfo_name
      
      @property
      def nfo_url(self) -> str:
        return self.__nfo_url

      def __str__(self) -> str:
        return f'{self.dirname} {self.nfo_name} {self.nfo_url}'


def get_nfo_name(files: list[any]) -> str | None:
    pattern: str = r".*\.nfo$"
    for file in files:
        if re.match(pattern, file.get('name')):
            return file.get('name')
    return None


def find_nfo_file(directory: str) -> str | None:
    for filename in os.listdir(directory):
        if re.match(r'.*\.nfo$', filename):
            return os.path.join(directory, filename)
    return None


def get_nfo_details(dirname: str) -> NfoDetails:
    url: str = f'https://api.srrdb.com/v1/nfo/{dirname}'
    response: requests.Response = requests.get(url)
    if response.status_code != 200:
        logging.error(f'Request failed: {response.status_code}')
        sys.exit(1)
    json_content: dict = json.loads(response.text)
    return NfoDetails(json_content.get('release'), json_content.get('nfo')[0], json_content.get('nfolink')[0])


def replace_nfo(original_nfo_path: str, nfo_details: NfoDetails, destination: str) -> None:
    new_nfo_file: str = os.path.join(destination, nfo_details.nfo_name)
    download_nfo(nfo_details.nfo_url, new_nfo_file)
    os.remove(original_nfo_path)


def download_nfo(nfo_url: str, destination: str) -> None:
    response: requests.Response = requests.get(nfo_url)
    if response.status_code != 200:
        logging.error(f'Request failed: {response.status_code}')
        sys.exit(1)
    with open(destination, 'wb') as f:
        f.write(response.content)


def is_nfo_mismatch(original_nfo_path: str, nfo_details: NfoDetails) -> bool:
    original_nfo_filename: str = os.path.basename(original_nfo_path)
    return original_nfo_filename != nfo_details.nfo_name


def main():
    parser = argparse.ArgumentParser(description='replace nfo file')
    parser.add_argument('-p', '--path', type=str, help='path to dirname')
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        logging.error(f'File not found: {args.path}')
        sys.exit(1)

    original_nfo_path: str | None = find_nfo_file(args.path)
    logging.debug(f'original_nfo_path: {original_nfo_path}')
    dirname: str = os.path.basename(args.path)
    logging.debug(f'dirname: {dirname}')
    nfo_details: NfoDetails = get_nfo_details(dirname)
    logging.debug(f'nfo details: {nfo_details}')

    if is_nfo_mismatch(original_nfo_path, nfo_details):
        logging.info(f'Replace nfo in: {args.path}')
        replace_nfo(original_nfo_path, nfo_details, args.path)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
    sys.exit(0)
