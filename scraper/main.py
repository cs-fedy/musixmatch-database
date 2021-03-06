import psycopg2
from dotenv import load_dotenv
from scraper.data_scraper import ScrapeMusixMatch
import tabulate
import os
import uuid

load_dotenv(dotenv_path=r"../.env")


# TODO: store lyrics and translations using AWS


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
                    artist_id INT NOT NULL ON DELETE CASCADE,
                    genre_label TEXT NOT NULL,
                    FOREIGN KEY (artist_id) REFERENCES artist(artist_id)); 
        '''
        queries.append((genre_table_query, "genre"))
        # album(album_id_, artist_id*, album_pict, album_title, album_release_date)
        album_table_query = '''
                CREATE TABLE album(
                    album_id INT PRIMARY KEY NOT NULL,
                    artist_id INT NOT NULL ON DELETE CASCADE,
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
                    album_id INT NOT NULL ON DELETE CASCADE,
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
                    song_id INT NOT NULL ON DELETE CASCADE,
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

    def __check_existence(self, column_name, column_value, table_name):
        check_query = f"SELECT {column_name} FROM {table_name} WHERE {column_name} == {column_value}"
        self.cursor.execute()
        return len(self.cursor.fetchall()) != 0

    def __seed_genre_table(self, artist_id, genres_list):
        for genre in genres_list:
            if self.__check_existence("genre_label", genre, "genre"):
                return

            genre_id = f"genre:{uuid.uuid1()}"
            while self.__check_existence("genre_id", genre_id, "genre"):
                genre_id = f"genre:{uuid.uuid1()}"

            seeding_genre_query = f""" 
                    INSERT INTO artist (genre_id, artist_id, genre_label)  
                    VALUES ({genre_id}, {artist_id}, {genre})
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
        for song in songs:
            song_id = f"song:{uuid.uuid1()}"
            while self.__check_existence("song_id", song_id, "song"):
                song_id = f"song:{uuid.uuid1()}"

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

        for translation in translations_list:
            translation_id = f"translation:{uuid.uuid1()}"
            while self.__check_existence("translation_id", translation_id, "translation"):
                translation_id = f"translation:{uuid.uuid1()}"

            language, lyrics = translation.values()
            seeding_translation_query = f""" 
                    INSERT INTO artist (translation_id, song_id, translation_language, translation)  
                    VALUES ({translation_id}, {song_id}, {language}, {lyrics})
            """
            self.cursor.execute(seeding_translation_query)
            self.connection.commit()
            print(f"seeding translation table with {song_title} translation to {language=} details done")

    def __seed_album_table(self, artist_id, albums):
        for album in albums:
            album_id = f"album:{uuid.uuid1()}"
            while self.__check_existence("album_id", album_id, "album"):
                album_id = f"album:{uuid.uuid1()}"

            album_picture, album_title, songs_data, album_release_date = album.values()
            seeding_album_query = f""" 
                    INSERT INTO artist (album_id, artist_id, album_pict, album_title, album_release_date)  
                    VALUES ({album_id}, {artist_id}, {album_picture}, {album_title}, {album_release_date})
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
        for artist in smm():
            artist_id = f"artist:{uuid.uuid1()}"
            while self.__check_existence("artist_id", artist_id, "artist"):
                artist_id = f"artist:{uuid.uuid1()}"

            artist_details, artist_albums = artist.values()
            # seed artist table with artist details
            self.__seed_artist_table(artist_id, artist_details)
            # seed albums table with artist's albums
            self.__seed_album_table(artist_id, artist_albums)
            print("\n")

    def __drop_tables(self, tables_names):
        for table_name in tables_names:
            drop_table_query = f"DROP TABLE IF EXISTS {table_name} CASCADE"
            self.cursor.execute(drop_table_query)
            self.connection.commit()
            print(f"table {table_name} dropped")

    def __get_data(self, table_name):
        if not self.connection:
            return

        row_select_query = f"SELECT * FROM {table_name}"
        self.cursor.execute(row_select_query)
        rows = [row[0] for row in self.cursor.fetchall()]
        columns_select_query = f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';"
        self.cursor.execute(columns_select_query)
        columns = [col[0] for col in self.cursor.fetchall()]
        print("="*28, f"@ rows in {table_name} table @", "="*28)
        print(tabulate.tabulate(rows, headers=columns, tablefmt="psql"))
        print("\n")

    def __call__(self):
        self.__connect()
        self.__drop_tables(["album", "artist", "genre", "song", "song_translation"])
        self.__create_tables()
        self.__seed_db()
        self.__get_data("album")
        self.__close_connection()


if __name__ == "__main__":
    db = DB()
    db()
