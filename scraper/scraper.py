from selenium import webdriver
from bs4 import BeautifulSoup
from helpers import *
import json


# TODO: fix encoding problem: extracting data using beautifulSoup
# TODO: fix element is not clickable and get all translations urls
# TODO: fix element is not clickable and get all albums


class ScrapeMusixMatch:
    def __init__(self, browser=None):
        self.url = "https://www.musixmatch.com/artists/"
        if not browser:
            self.browser = create_headless_browser()
        else:
            self.browser = browser

    def __get_category_data(self, url):
        source_code = load_full_page(self.browser, url)
        soup = BeautifulSoup(source_code, "html.parser")
        artists_links = [f"https://www.musixmatch.com{artist['href']}"
                         for artist in soup.select(".mxm-artist-index-link a")]
        artists_data = []
        for link in artists_links:
            sap = ScrapeArtistsProfile(link, self.browser)
            artists_data.append(sap())
        return artists_data

    def __call__(self):
        categories_urls = [f"{self.url}{chr(c + 65)}" for c in range(26)]
        categories_urls.append(f"{self.url}0-9")
        categories_data = []
        for category in categories_urls:
            categories_data.extend(self.__get_category_data(category))
        return categories_data


if __name__ == "__main__":
    headless_browser = create_headless_browser()
    sam = ScrapeMusixMatch(headless_browser)

    with open(r"data.json", mode="w+") as file:
        json.dump(sam(), file)
