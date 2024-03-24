#!/usr/bin/env python

import json
import logging
import argparse
import requests
from pathlib import Path


class Configuration:
    def __init__(self, username: str, password: str, api_key: str):
        self.__username: str = username
        self.__password: str = password
        self.__api_key: str = api_key

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password(self) -> str:
        return self.__password

    @property
    def api_key(self) -> str:
        return self.__api_key


class ConfigurationService:
    def __init__(self, configuration_path: str):
        if not Path(configuration_path).exists():
            raise FileNotFoundError(f'Could not find configuration file: {configuration_path}')
        self.__configuration: dict = json.load(open(configuration_path))

    def get_configuration(self) -> Configuration:
        return Configuration(self.__configuration['username'],
                             self.__configuration['password'],
                             self.__configuration['api_key'])


class PtpImageService:
    def __init__(self, configuration: Configuration, is_debug_mode: bool):
        self.__base_url: str = 'https://ptpimg.me'
        self.__is_debug_mode: bool = is_debug_mode
        self.__proxy: dict = {}
        if self.__is_debug_mode:
            self.__proxy = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
        self.__configuration: Configuration = configuration
        self.__session: requests.Session = requests.Session()
        self.__authenticate()

    def __authenticate(self) -> None:
        credentials: dict = {
            'email': self.__configuration.username,
            'pass': self.__configuration.password,
            'login': '',
        }
        response: requests.Response = self.__session.post(
            f'{self.__base_url}/login.php', data=credentials, allow_redirects=True,
            proxies=self.__proxy, verify=not self.__is_debug_mode)

        if response.status_code != 200:
             raise requests.exceptions.HTTPError(f'Could not authenticate. Response code: {response.status_code}')

        if '/logout.php' not in response.text:
            raise ValueError('Could not authenticate successful. Response code: {response.status_code}')

    def __get_image_url(self, image: dict) -> str:
        """
        an image in the result looks like this
        {
            "code": "5ts2wy",
            "ext": "png"
        },
        """

        return f"{self.__base_url}/{image['code']}.{image['ext']}"

    def __get_multipart_from_from_images(self, images: list[Path]) -> dict:
        multipart_form_data: dict = {}
        for i in range(len(images)):
            multipart_form_data[f'file-upload[{i}]'] = (images[i].name, open(images[i], 'rb'), 'image/png')

        return multipart_form_data

    def upload(self, images: list[Path]) -> list[str]:
        for image in images:
            if not image.exists():
                raise ValueError(f'Can not upload images. Image {image} does not exist!')

        multipart_form_data: dict = self.__get_multipart_from_from_images(images)
        data: dict = {'api_key': self.__configuration.api_key}

        # WARNING: UPLOAD DOES NOT WORK WHEN USING BURP WITH --debug!
        response: requests.Response = self.__session.post(
            f'{self.__base_url}/upload.php', files=multipart_form_data,
            data=data, proxies=self.__proxy, verify=not self.__is_debug_mode)

        if response.status_code != 200:
             raise requests.exceptions.HTTPError(f'Upload failed. Response code: {response.status_code}')

        upload_result: dict = json.loads(response.content)

        return [self.__get_image_url(image) for image in upload_result]


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--directory', required=True, type=str, help='image directory')
    argparser.add_argument('--configuration', required=True, type=str, help='path to json config')
    argparser.add_argument('--debug', action='store_true', default=False, help='use burp proxy for debugging')
    args = argparser.parse_args()

    configuration: Configuration = ConfigurationService(args.configuration).get_configuration()
    ptp_image: PtpImageService = PtpImageService(configuration, args.debug)

    images: list[Path] = list(Path(args.directory).glob('*.png'))
    links: list[str] = ptp_image.upload(images)

    for link in links:
        print(f'[img]{link}[/img]')


if __name__ == '__main__':
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.basicConfig(
        level=logging.DEBUG, format='%(asctime)s [%(levelname)s] - %(message)s',
        datefmt='%m-%d-%Y %H:%M:%S')
    main()
