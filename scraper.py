from selenium import webdriver
from bs4 import BeautifulSoup
import json
import time


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
        self.__get_data()

    @staticmethod
    def __get_song_data(source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        # * get song title:
        song_title = soup.select_one(".mxm-track-title__track").getText()

        # * get song writer:
        song_writer = soup.select_one(".mxm-lyrics__copyright").getText()

        # * get artist name:
        artist_name = soup.select_one(".mxm-track-title__artist").getText()

        # * album details:
        album_name = soup.select_one(".mui-cell__title").getText()
        album_release_date = soup.select_one(".mui-cell__subtitle").getText()

        return {
            "song_title": song_title,
            "song_writer": song_writer,
            "artist_name": artist_name,
            "album_name": album_name,
            "album_release_date": album_release_date
        }

    @staticmethod
    def __get_song_lyrics(source_code):
        soup = BeautifulSoup(source_code, "html.parser")
        lyrics_elements = soup.select(".mxm-lyrics__content")
        lyrics = [lyrics_element.getText() for lyrics_element in lyrics_elements]
        return "\n".join(lyrics)

    def __get_translations_urls(self):
        # TODO: fix element is not clickable and get all translations urls
        soup = BeautifulSoup(self.browser.page_source, "html.parser")
        links_elements = soup.select(".other_translations a")[1:]
        links = [f"https://www.musixmatch.com{element['href']}" for element in links_elements]
        return links

    def __get_translations(self):
        translation_urls = self.__get_translations_urls()
        return [self.__get_translation_data(url) for url in translation_urls]

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

    def __get_data(self):
        source_code = load_full_page(self.browser, self.song_url)
        lyrics = self.__get_song_lyrics(source_code)
        song_details = self.__get_song_data(source_code)
        translations = self.__get_translations()
        data = {
            "default_lyrics": lyrics,
            "details": song_details,
            "translations": translations
        }
        with open(r"data.json", mode="w+") as file:
            json.dump(data, file)


if __name__ == "__main__":
    url = "https://www.musixmatch.com/lyrics/Disturbed/The-Sound-Of-Silence"
    headless_browser = create_headless_browser()
    ssl = ScrapeSongLyrics(url, headless_browser)
