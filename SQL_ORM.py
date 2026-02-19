__author__ = "Guy Mosseri"

import sqlite3


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
    def __init__(self, user_id, username, password):
        self.user_id = user_id
        self.username = username
        self.password = password

    def __str__(self):
        return f"{self.__dict__}"


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
        self.conn = sqlite3.connect('schedule.db')
        self.cursor = self.conn.cursor()

    def close_DB(self):
        if self.conn:
            self.conn.close()

    def commit(self):
        self.conn.commit()

    def execute(self, sql, *argv):
        self.cursor.execute(sql, *argv)

    def _ensure_tables(self):
        sqls = [
            """CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY,
                name TEXT,
                artist TEXT,
                album TEXT,
                release_date DATE,
                likes_count INTEGER,
                file_path TEXT
                );
            """,
            """CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                salt TEXT
                );
            """,
            """CREATE TABLE IF NOT EXISTS playlists (
                playlist_id INTEGER PRIMARY KEY,
                title TEXT,
                user_id INTEGER,
                creation_date DATE DEFAULT GETDATE(),
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
            """
        ]
        self.open_DB()
        for sql in sqls:
            self.execute(sql)
        self.commit()
        self.close_DB()

    # ----------- Users ----------- #
    def insert_user(self, user: User):
        sql = f"INSERT INTO users ({" ".join(user.__dict__.keys())}) VALUES ({",".join("?"*len(user.__dict__.keys()))})"
        self.open_DB()
        self.execute(sql, *user.__dict__.values())
        self.commit()
        self.close_DB()

    # ----------- Songs ----------- #
    def insert_song(self, song: Song):
        sql = f"INSERT INTO users ({" ".join(song.__dict__.keys())}) VALUES ({",".join("?"*len(song.__dict__.keys()))})"
        self.open_DB()
        self.execute(sql, *song.__dict__.values())
        self.commit()
        self.close_DB()

    # ----------- Playlists ----------- #
    def insert_playlist(self, playlist: Playlist):
        sql = f"INSERT INTO users ({" ".join(playlist.__dict__.keys())}) VALUES ({",".join("?"*len(playlist.__dict__.keys()))})"
        self.open_DB()
        self.execute(sql, *playlist.__dict__.values())
        self.commit()
        self.close_DB()

    # ----------- Playlist songs ----------- #
    def insert_playlist_song(self, playlist_song: Playlist_song):
        sql = f"INSERT INTO users ({" ".join(playlist_song.__dict__.keys())}) VALUES ({",".join("?"*len(playlist_song.__dict__.keys()))})"
        self.open_DB()
        self.execute(sql, *playlist_song.__dict__.values())
        self.commit()
        self.close_DB()
