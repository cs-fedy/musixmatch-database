from bs4 import BeautifulSoup
from scraper.helpers import *
from scraper.scrape_song_lyrics import ScrapeSongLyrics
import json


class ScrapeArtistsProfile:
    def __init__(self, artist_url, browser=None):
        self.artist_profile_url = artist_url
        self.albums_page_url = f"{self.artist_profile_url}/albums"
        if not browser:
            self.browser = create_headless_browser()
        else:
            self.browser = browser

    @staticmethod
    def __scrape_profile_details(source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        # * get profile picture
        profile_picture = soup.select_one(".profile-avatar")["src"]

        # * get profile name
        profile_name = soup.find_all("h1")[-1].getText()

        # * get profile status: verified or not
        status_element = soup.select_one(".verified")
        if status_element:
            status = "verified"
        else:
            status = "not verified"

        # * get genres
        genres_list = soup.select_one(".genres").findChildren()
        genres = list({genre.getText() for genre in genres_list})

        return {
            "profile_pict": profile_picture,
            "profile_name": profile_name,
            "status": status,
            "genres": genres
        }

    def __get_albums_details(self):
        load_full_page(self.browser, self.albums_page_url)
        # self.browser.find_element_by_css_selector(".load-more-pager").click()
        # time.sleep(1)
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        # * get albums data
        albums_urls = [f"https://www.musixmatch.com{album['href']}"
                       for album in soup.select(".media-card-title a")]
        return [self.__get_album_details(album_url) for album_url in albums_urls]

    def __get_album_details(self, album_url):
        source_code = load_full_page(self.browser, album_url)
        soup = BeautifulSoup(source_code, "html.parser")
        album_pict = soup.select_one(".mxm-album-banner__coverart img")["src"]

        album_title = soup.select_one(".mxm-album-banner__name").getText()
        album_release_date = soup.select_one(".mxm-album-banner__release")
        songs_urls = [f"https://www.musixmatch.com{song['href']}"
                      for song in soup.select(".mxm-album__tracks .mui-collection__item a")]
        songs_data = []
        for song_url in songs_urls:
            ssl = ScrapeSongLyrics(song_url, self.browser)
            songs_data.append(ssl())

        return {
            "album_picture": album_pict,
            "album_title": album_title,
            "songs_data": songs_data,
            "album_release_date": album_release_date
        }

    def __call__(self):
        source_code = load_full_page(self.browser, self.artist_profile_url)
        profile_details = self.__scrape_profile_details(source_code)
        albums_details = self.__get_albums_details()
        return {
            "profile_details": profile_details,
            "albums_details": albums_details
        }


if __name__ == "__main__":
    headless_browser = create_headless_browser()
    url = "profile url"
    sap = ScrapeArtistsProfile(url, headless_browser)

    with open(r"data.json", mode="w+") as file:
        json.dump(sap(), file)
