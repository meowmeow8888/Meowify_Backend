__author__ = "Guy Mosseri"

import sqlite3
from datetime import datetime


class Song:
    def __init__(self, song_id, name, artist, album, release_date, likes_count, file_path):
        self.song_id = song_id
        self.name = name
        self.artist = artist
        self.album = album
        self.release_date = release_date
        self.likes_count = likes_count
        self.file_path = file_path

    def __str__(self):
        return f"{self.__dict__}"


class User:
    def __init__(self, user_id, email, password, salt):
        self.user_id = user_id
        self.email = email
        self.password = password
        self.salt = salt

    def __str__(self):
        return f"{self.__dict__}"


class Verification_info:
    def __init__(self, user_id, code, time=datetime.now()):
        self.user_id = user_id
        self.code = code
        self.time = time


class Playlist:
    def __init__(self, playlist_id, title, user_id, creation_date):
        self.playlist_id = playlist_id
        self.title = title
        self.user_id = user_id
        self.creation_date = creation_date

    def __str__(self):
        return f"{self.__dict__}"


class Playlist_song:
    def __init__(self, playlist_id, song_id, position):
        self.playlist_id = playlist_id
        self.song_id = song_id
        self.position = position

    def __str__(self):
        return f"{self.__dict__}"


class App_ORM:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self._ensure_tables()

    def open_DB(self):
        self.conn = sqlite3.connect(
    "Meowify.db",
    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
)
        self.cursor = self.conn.cursor()

    def close_DB(self):
        if self.conn:
            self.conn.close()

    def commit(self):
        self.conn.commit()

    def execute(self, sql, *argv):
        self.cursor.execute(sql, argv)

    def _ensure_tables(self):
        sqls = [
            """CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                artist TEXT,
                album TEXT,
                release_date DATE,
                likes_count INTEGER,
                file_path TEXT
                );
            """,
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                password TEXT,
                salt TEXT
                );
            """,
            """CREATE TABLE IF NOT EXISTS playlists (
                playlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                user_id INTEGER,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """,
            """CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER,
                song_id INTEGER,
                position INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id),
                FOREIGN KEY (song_id) REFERENCES songs(song_id)
                );
            """,
            """CREATE TABLE IF NOT EXISTS verification_info (
                user_id INTEGER,
                code TEXT,
                time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """
        ]
        self.open_DB()
        for sql in sqls:
            self.execute(sql)
        self.commit()
        self.close_DB()

    # ----------- General ----------- #
    def _insert_item(self, item):
        sql = f"INSERT INTO users ({", ".join(item.__dict__.keys())}) VALUES ({", ".join("?" * len(item.__dict__.keys()))})"
        self.open_DB()
        self.execute(sql, *item.__dict__.values())
        self.commit()
        self.close_DB()

    # ----------- Users ----------- #
    def insert_user(self, user: User):
        self._insert_item(dict(list(user.__dict__.items())[1:]))

    def get_user_by_email(self, email) -> User:
        sql = "SELECT * FROM users WHERE email=?"
        self.open_DB()
        self.execute(sql, email)
        row = self.cursor.fetchone()
        self.close_DB()
        return User(*row)

    # ----------- Songs ----------- #
    def insert_song(self, song: Song):
        self._insert_item(dict(list(song.__dict__.items())[1:]))

    def get_song_id(self, name, artist):
        sql = "SELECT song_id FROM songs WHERE name=? AND artist=?"
        self.open_DB()
        self.execute(sql, name, artist)
        song_id = self.cursor.fetchone()
        self.close_DB()
        return song_id

    def get_song_by_id(self, song_id):
        sql = "SELECT * FROM songs WHERE song_id=?"
        self.open_DB()
        self.execute(sql, song_id)
        song = self.cursor.fetchone()
        self.close_DB()
        return Song(*song)

    def increase_likes_count(self, song_id):
        sql = "UPDATE songs SET likes_count=likes_count+1 WHERE song_id=?"
        self.open_DB()
        self.execute(sql, song_id)
        self.close_DB()

    # ----------- Playlists ----------- #
    def insert_playlist(self, playlist: Playlist):
        self._insert_item(dict(list(playlist.__dict__.items())[1:]))

    # ----------- Playlist songs ----------- #
    def insert_playlist_song(self, playlist_song: Playlist_song):
        self._insert_item(playlist_song)

    # ----------- Verification info ----------- #
    def insert_verification_info(self, verification_info: Verification_info):
        self._insert_item(verification_info)
