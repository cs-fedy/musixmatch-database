from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time


# TODO: fix encoding problem: extracting data using beautifulSoup
# TODO: fix element is not clickable and get all translations urls
# TODO: fix element is not clickable and get all albums


def create_headless_browser():
    # options = Options()
    # options.set_headless()
    # assert options.headless  # assert Operating in headless mode
    # return webdriver.Chrome(options=options)
    return webdriver.Chrome()


def load_full_page(browser, page_url):
    browser.get(page_url)
    time.sleep(5)
    print(f"@@@ {page_url} is loaded @@@")
    return browser.page_source


class ScrapeSongLyrics:
    def __init__(self, song_url, browser=None):
        self.song_url = song_url
        if not browser:
            self.browser = create_headless_browser()
        else:
            self.browser = browser

    @staticmethod
    def __get_song_data(source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        # * get song title:
        song_title = soup.select_one("h1").getText()

        # * get song writer:
        song_writer = soup.select_one(".mxm-lyrics__copyright").getText()

        return {
            "song_title": song_title,
            "song_writer": song_writer
        }

    @staticmethod
    def __get_song_lyrics(source_code):
        if "Instrumental" in source_code:
            return "Instrumental"
        elif "Lyrics not available." in source_code:
            return "Lyrics not available."

        soup = BeautifulSoup(source_code, "html.parser")
        lyrics_elements = soup.select(".mxm-lyrics__content")
        lyrics = [lyrics_element.getText() for lyrics_element in lyrics_elements]
        return "\n".join(lyrics)

    def __get_translations_urls(self):
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        return [f"https://www.musixmatch.com{link['href']}"
                for link in soup.select(".base_translations a")
                if "translations" not in link]

    def __get_translations(self):
        translation_urls = self.__get_translations_urls()
        return [self.__get_translation_data(translation_url) for translation_url in translation_urls]

    def __get_translation_data(self, translation_url):
        source_code = load_full_page(self.browser, translation_url)
        soup = BeautifulSoup(source_code, "html.parser")
        # * get language translated to
        language_element_text = soup.find_all("h3")[1].getText()
        language = " ".join(language_element_text.split()[2:])

        # get translated lyrics
        lyrics_elements = soup.select(".mxm-translatable-line-readonly .row div")
        mixed_lyrics = [f"{element.getText()}" for element in lyrics_elements]
        lyrics = [mixed_lyrics[0]]
        for verse in mixed_lyrics[1:]:
            if verse != lyrics[-1]:
                lyrics.append(verse)

        return {
            "language": language,
            "lyrics": "\n".join(lyrics[1::2])
        }

    def __call__(self):
        source_code = load_full_page(self.browser, self.song_url)
        lyrics = self.__get_song_lyrics(source_code)
        song_details = self.__get_song_data(source_code)
        if lyrics == "Instrumental" or lyrics == "Lyrics not available.":

            translations = "undefined"
        else:
            translations = self.__get_translations()

        return {
            "default_lyrics": lyrics,
            "details": song_details,
            "translations": translations
        }


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
            "album_pictures": album_pict,
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
            "album_details": albums_details
        }


class ScrapeMusixMatch:
    def __init__(self, browser=None):
        self.url = "https://www.musixmatch.com/artists/"
        if not browser:
            self.browser = create_headless_browser()
        else:
            self.browser = browser
        self.__get_data()

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

    def __get_data(self):
        categories_urls = [f"{self.url}{chr(c + 65)}" for c in range(26)]
        categories_data = []
        for category in categories_urls:
            categories_data.extend(self.__get_category_data(category))

        with open(r"data.json", mode="w+") as file:
            json.dump(categories_data, file)


if __name__ == "__main__":
    headless_browser = create_headless_browser()
    sam = ScrapeMusixMatch(headless_browser)
