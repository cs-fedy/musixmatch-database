import psycopg2
from dotenv import load_dotenv
from scraper.scraper import ScrapeMusixMatch
import os

load_dotenv(dotenv_path=r"../.env")


# TODO: store lyrics and translations using AWS
# TODO: refactor schema
# TODO: add on delete cascade to db schema
# TODO: debug the script


class DB:
    def __init__(self):
        self.__POSTGRES_DB = os.getenv("POSTGRES_DB")
        self.__POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.__POSTGRES_USER = os.getenv("POSTGRES_USER")

    def __connect(self):
        try:
            self.connection = psycopg2.connect(user=self.__POSTGRES_USER,
                                               password=self.__POSTGRES_PASSWORD,
                                               host="127.0.0.1",
                                               port="5432",
                                               database=self.__POSTGRES_DB)
            self.cursor = self.connection.cursor()
            print("connected to db successfully")
        except (Exception, psycopg2.Error) as error:
            print("failed to connect to db", error)

    def __create_tables(self):
        if not self.connection:
            return
        queries = []
        # artist(artist_id_, artist_picture, artist_status, artist_name)
        artist_table_query = '''
                CREATE TABLE artist(
                    artist_id INT PRIMARY KEY NOT NULL,
                    artist_picture TEXT,
                    artist_status TEXT,
                    artist_name TEXT NOT NULL); 
        '''
        queries.append((artist_table_query, "artist"))
        # genre(artist_id*, genre_label)
        genre_table_query = '''
                CREATE TABLE genre(
                    genre_id INT PRIMARY KEY NOT NULL,
                    artist_id INT NOT NULL,
                    genre_label TEXT NOT NULL,
                    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)); 
        '''
        queries.append((genre_table_query, "genre"))
        # album(album_id_, artist_id*, album_pict, album_title, album_release_date)
        album_table_query = '''
                CREATE TABLE album(
                    album_id INT PRIMARY KEY NOT NULL,
                    artist_id INT NOT NULL,
                    album_pict TEXT,
                    album_title TEXT NOT NULL,
                    album_release_data TEXT,
                    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)); 
        '''
        queries.append((album_table_query, "album"))
        # song(song_id_, album_id*, song_title, song_writer, song_lyrics)
        song_table_query = '''
                CREATE TABLE song(
                    song_id INT PRIMARY KEY NOT NULL,
                    album_id INT NOT NULL,
                    song_title TEXT NOT NULL,
                    song_writer TEXT,
                    song_lyrics TEXT NOT NULL,
                    FOREIGN KEY (album_id) REFERENCES album(album_id)); 
        '''
        queries.append((song_table_query, "song"))
        # song_translation(translation_id_, song_id*, translation_language, translation)
        song_translation_table_query = '''
                CREATE TABLE song_translation(
                    translation_id INT PRIMARY KEY NOT NULL,
                    song_id INT NOT NULL,
                    translation_language TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    FOREIGN KEY (song_id) REFERENCES song(song_id)); 
        '''
        queries.append((song_translation_table_query, "song_translation"))

        for query in queries:
            query_text, table_name = query
            self.cursor.execute(query_text)
            self.connection.commit()
            print(f"Table {table_name} created successfully in PostgreSQL ")

    def __close_connection(self):
        if not self.connection:
            return

        self.cursor.close()
        self.connection.close()
        print("PostgreSQL connection is closed")

    def __seed_genre_table(self, artist_id, genres_list):
        for index, genre in enumerate(genres_list):
            seeding_genre_query = f""" 
                    INSERT INTO artist (genre_id, artist_id, genre_label)  
                    VALUES ({index}, {artist_id}, {genre})
            """

            self.cursor.execute(seeding_genre_query)
            self.connection.commit()
        print(f"seeding genre table with {' '.join(genres_list)}")

    def __seed_artist_table(self, index, details):
        profile_pict, profile_name, status, genres = details.values()
        seeding_artist_query = f""" 
                INSERT INTO artist (artist_id, artist_picture, artist_status, artist_name)  
                VALUES ({index},{profile_pict}, {status}, {profile_name})
        """
        self.cursor.execute(seeding_artist_query)
        self.connection.commit()

        # seed genre table with genres
        self.__seed_genre_table(index, genres)
        print(f"seeding artist table with {profile_name} details done")

    def __seed_song_table(self, album_id, songs):
        for song_id, song in enumerate(songs):
            default_lyrics, details, translations = song.values()
            song_title, song_writer = details.values()
            seeding_song_query = f""" 
                    INSERT INTO artist (song_id, album_id, song_title, song_writer, song_lyrics)  
                    VALUES ({song_id},{album_id}, {song_title}, {song_writer}, {default_lyrics})
            """
            self.cursor.execute(seeding_song_query)
            self.connection.commit()

            # seed translation table with songs translations
            self.__seed_translation_table(song_id, song_title, translations)
            print(f"seeding song table with {song_title} details done")

    def __seed_translation_table(self, song_id, song_title, translations):
        if isinstance(translations, str):
            translations_list = [translations]
        else:
            translations_list = translations

        for translation_id, translation in enumerate(translations_list):
            language, lyrics = translation.values()
            seeding_translation_query = f""" 
                    INSERT INTO artist (translation_id, song_id, translation_language, translation)  
                    VALUES ({translation_id}, {song_id}, {language}, {lyrics})
            """
            self.cursor.execute(seeding_translation_query)
            self.connection.commit()
            print(f"seeding song table with {song_title} translation to {language=} details done")

    def __seed_album_table(self, index, albums):
        for album_id, album in enumerate(albums):
            album_picture, album_title, songs_data, album_release_date = album.values()
            seeding_album_query = f""" 
                    INSERT INTO artist (album_id, artist_id, album_pict, album_title, album_release_date)  
                    VALUES ({index},{album_id}, {index}, {album_picture}, {album_title}, {album_release_date})
            """
            self.cursor.execute(seeding_album_query)
            self.connection.commit()

            # seed songs table with album songs
            self.__seed_song_table(album_id, songs_data)
            print(f"seeding album table with {album_title} album done")

    def __seed_db(self):
        if not self.connection:
            return

        smm = ScrapeMusixMatch()
        for index, artist in enumerate(smm()):
            artist_details, artist_albums = artist.values()
            # seed artist table with artist details
            self.__seed_artist_table(index, artist_details)
            # seed albums table with artist's albums
            self.__seed_album_table(index, artist_albums)
            print("\n")

    def __call__(self):
        self.__connect()
        self.__create_tables()
        self.__seed_db()
        self.__close_connection()


if __name__ == "__main__":
    db = DB()
    db()
