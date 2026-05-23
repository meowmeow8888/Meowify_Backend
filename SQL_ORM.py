__author__ = "Guy Mosseri"

import sqlite3
from datetime import datetime


class Song:
    def __init__(self, song_id, name, artist, album, release_date, likes_count, song_path, thumbnail_path):
        self.song_id = song_id
        self.name = name
        self.artist = artist
        self.album = album
        self.release_date = release_date
        self.likes_count = likes_count
        self.song_path = song_path
        self.thumbnail_path = thumbnail_path

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

    def __eq__(self, other):
        return self.email == other.email and self.password == other.password


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


class Session:
    def __init__(self, session_id, user_id, created_at, last_seen):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at:datetime = created_at
        self.last_seen = last_seen


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
                song_path TEXT,
                thumbnail_path TEXT
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
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """,
            """CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
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
        sql = """
            INSERT INTO users (email, password, salt)
            VALUES (?, ?, ?)
        """
        self.open_DB()
        self.execute(sql, user.email, user.password, user.salt)
        self.commit()
        self.close_DB()

    def get_user_by_email(self, email) -> User:
        sql = "SELECT * FROM users WHERE email=?"
        self.open_DB()
        self.execute(sql, email)
        row = self.cursor.fetchone()
        self.close_DB()
        return User(*row) if row else None

    def user_exists(self, email) -> bool:
        user = self.get_user_by_email(email)
        if user:
            return True
        return False

    def get_user_by_id(self, user_id):
        sql = "SELECT * FROM users WHERE user_id=?"
        self.open_DB()
        self.execute(sql, user_id)
        row = self.cursor.fetchone()
        self.close_DB()
        return User(*row)

    # ----------- Songs ----------- #
    def insert_song(self, song: Song):
        sql = """
            INSERT INTO songs (name, artist, album, release_date, likes_count, song_path, thumbnail_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.open_DB()
        self.execute(sql,
                     song.name,
                     song.artist,
                     song.album,
                     song.release_date,
                     song.likes_count,
                     song.song_path,
                     song.thumbnail_path
                     )
        self.commit()
        self.close_DB()

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
        return Song(*song) if song else None

    def get_song_path(self, name, artist):
        sql = "SELECT song_path FROM songs WHERE name=? AND artist=?"
        self.open_DB()
        self.execute(sql, name, artist)
        song_path = self.cursor.fetchone()
        self.close_DB()
        return song_path[0] if song_path else None

    def increase_likes_count(self, song_id):
        sql = "UPDATE songs SET likes_count=likes_count+1 WHERE song_id=?"
        self.open_DB()
        self.execute(sql, song_id)
        self.close_DB()

    def search_close_songs(self, query):
        sql = "SELECT name FROM songs WHERE LOWER(name) LIKE ? ORDER BY likes_count DESC LIMIT 5"
        self.open_DB()
        self.execute(sql, f"%{query.lower()}%")
        names = [row[0] for row in self.cursor.fetchall()]
        self.close_DB()
        return names

    def get_song_info_by_name(self, name):
        sql = "SELECT * FROM songs WHERE name=?"
        self.open_DB()
        self.execute(sql, name)
        song = self.cursor.fetchone()
        self.close_DB()
        return Song(*song) if song else None

    def get_top_songs(self):
        sql = "SELECT * FROM songs ORDER BY likes_count DESC LIMIT 5"
        self.open_DB()
        self.execute(sql)
        songs = self.cursor.fetchall()
        self.close_DB()
        return [Song(*s) for s in songs]

    # ----------- Playlists ----------- #
    def insert_playlist(self, playlist: Playlist):
        sql = """
            INSERT INTO playlists (title, user_id, creation_date)
            VALUES (?, ?, ?)
        """
        self.open_DB()
        self.execute(sql,
                     playlist.title,
                     playlist.user_id,
                     playlist.creation_date
                     )
        self.commit()
        self.close_DB()

    # ----------- Playlist songs ----------- #
    def insert_playlist_song(self, playlist_song: Playlist_song):
        sql = """
            INSERT INTO playlist_songs (playlist_id, song_id, position)
            VALUES (?, ?, ?)
        """
        self.open_DB()
        self.execute(sql,
                     playlist_song.playlist_id,
                     playlist_song.song_id,
                     playlist_song.position
                     )
        self.commit()
        self.close_DB()

    # ----------- Verification info ----------- #
    def insert_verification_info(self, verification_info: Verification_info):
        sql = """
            INSERT INTO verification_info (user_id, code, time)
            VALUES (?, ?, ?)
        """
        self.open_DB()
        self.execute(sql,
                     verification_info.user_id,
                     verification_info.code,
                     verification_info.time
                     )
        self.commit()
        self.close_DB()

    def get_verification_info_by_user_id(self, user_id):
        sql = "SELECT * FROM verification_info WHERE user_id=?"
        self.open_DB()
        self.execute(sql, user_id)
        row = self.cursor.fetchone()
        self.close_DB()
        return Verification_info(*row) if row else None

    def del_verification_info_by_user_id(self, user_id):
        sql = "DELETE FROM verification_info WHERE user_id=?"
        self.open_DB()
        self.execute(sql, user_id)
        self.commit()
        self.close_DB()

    # ----------- Sessions ----------- #
    def insert_session(self, session_id, user_id):
        sql = "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)"
        self.open_DB()
        self.execute(sql, session_id, user_id)
        self.commit()
        self.close_DB()

    def get_session(self, session_id):
        sql = "SELECT * FROM sessions WHERE session_id=?"
        self.open_DB()
        self.execute(sql, session_id)
        row = self.cursor.fetchone()
        self.close_DB()
        return Session(*row) if row else None

    def update_last_seen(self, session_id, user_id, last_seen):
        sql = "UPDATE sessions SET last_seen=? WHERE session_id=? AND user_id=?"
        self.open_DB()
        self.execute(sql, last_seen, session_id, user_id)
        self.commit()
        self.close_DB()