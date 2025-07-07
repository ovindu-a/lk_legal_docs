import os
import shutil
import time
from functools import cache, cached_property

import requests
from bs4 import BeautifulSoup
from utils import File, Hash, Log

from utils_future import Directory


class WebPage:
    BASE_URL = "https://documents.gov.lk"
    T_SLEEP = 5
    T_TIMEOUT = 60
    DIR_HTML_CACHE = "html_cache"

    def __init__(self, url):
        assert url.startswith(self.BASE_URL)
        self.url = url
        self.__session__ = requests.Session()
        self.log = Log(f"🌐 {self.url}")

    def __get_response__(self):
        t_start = time.time()
        response = self.__session__.get(self.url, timeout=WebPage.T_TIMEOUT)
        delta_t = (time.time() - t_start) * 1000
        self.log.debug(
            f"{response.status_code} {response.reason}, {delta_t:,.0f}ms"
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
        self.log.debug(f" -> {self.local_content_path}")
        return content

    @staticmethod
    def delete_html_cache():
        shutil.rmtree(WebPage.DIR_HTML_CACHE, ignore_errors=True)
        Log("WebPage").warning(f"❌ Deleted {WebPage.DIR_HTML_CACHE}")

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
        self.log.debug(f"Wrote {file_path} ({file_size_k:.1f} KB)")
