from scraper.helpers import *
from bs4 import BeautifulSoup
import json


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


if __name__ == "__main__":
    headless_browser = create_headless_browser()
    url = "song url"
    ssl = ScrapeSongLyrics(url, headless_browser)

    with open(r"data.json", mode="w+") as file:
        json.dump(ssl(), file)
