import os
import shutil
from functools import cache, cached_property

import requests
from bs4 import BeautifulSoup
from utils import File, Hash, Log

from utils_future import Directory

log = Log("WebPage")


class WebPage:
    BASE_URL = "https://documents.gov.lk"
    T_TIMEOUT = 240
    DIR_HTML_CACHE = "html_cache"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        + " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36"
    }

    def __init__(self, url):
        assert url.startswith(self.BASE_URL)
        self.url = url
        self.__session__ = requests.Session()

    def __get_response__(self):
        response = self.__session__.get(
            self.url, headers=WebPage.HEADERS, timeout=WebPage.T_TIMEOUT
        )
        response.raise_for_status()
        return response

    @cached_property
    def hash(self):
        return Hash.md5(self.url)[:8]

    @cached_property
    def local_content_path(self):
        return os.path.join(self.DIR_HTML_CACHE, f"{self.hash}")

    @cached_property
    def content_hot(self):
        response = self.__get_response__()
        return response.text

    @cached_property
    def content(self):
        os.makedirs(self.DIR_HTML_CACHE, exist_ok=True)
        if os.path.exists(self.local_content_path):
            return File(self.local_content_path).read()
        content = self.content_hot
        File(self.local_content_path).write(content)
        return content

    @staticmethod
    def delete_html_cache():
        shutil.rmtree(WebPage.DIR_HTML_CACHE, ignore_errors=True)
        log.warning(f"❌ Deleted {WebPage.DIR_HTML_CACHE}")

    @staticmethod
    @cache
    def get_html_cache_size() -> int:
        return Directory(WebPage.DIR_HTML_CACHE).size

    @cached_property
    def soup(self):
        return BeautifulSoup(self.content, "html.parser")

    def download_binary(self, file_path):
        response = self.__get_response__()
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        file_size_k = os.path.getsize(file_path) / (1_000)
        log.debug(f"Wrote {file_path} ({file_size_k:.1f} KB)")
