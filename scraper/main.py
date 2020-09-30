import psycopg2
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=r"../.env")


# TODO: store lyrics and translations using AWS
# TODO: refactor schema
# TODO: add on delete cascade to db schema


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

    def __call__(self):
        self.__connect()
        self.__create_tables()
        self.__close_connection()


if __name__ == "__main__":
    db = DB()
    db()
