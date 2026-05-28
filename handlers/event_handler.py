import base64
import json
import threading
from datetime import datetime
import time

from SQL_ORM import App_ORM, Song
from services.audio_streamer import AudioStreamer
from queue import Queue
from websocket import websocket, wsMsg
from services.song_scrapper import download_multiple


class Instruction:
    def __init__(self, inst, **params):
        self.inst = inst
        self.params = params


class Event_Handler:
    db = App_ORM()
    Lock = threading.Lock()

    @staticmethod
    def event_loop(ws: websocket, instruction_queue: Queue[Instruction]):
        audio_streamer: AudioStreamer | None = None
        playing = False
        last_state_update = 0

        while True:
            try:
                if not instruction_queue.empty():
                    inst = instruction_queue.get()
                    if inst.inst == "start_streaming":
                        song_name = inst.params.get("song_name")
                        artist = inst.params.get("artist")
                        with Event_Handler.Lock:
                            song_path = Event_Handler.db.get_song_path(song_name, artist)

                        audio_streamer = AudioStreamer(song_path)
                        playing = True
                        ws.send(
                            wsMsg.text(json.dumps({"type": "song_start", "song_len": str(audio_streamer.duration)})))
                        instruction_queue.put(Instruction("need_chunk", **{}))

                    elif inst.inst == "pause":
                        playing = False

                    elif inst.inst == "resume":
                        playing = True

                    elif inst.inst == "stop":
                        playing = False
                        audio_streamer = None

                    elif inst.inst == "seek":
                        if audio_streamer:
                            position = inst.params.get("position", 0)
                            print(position, " - new position")
                            audio_streamer.jump_to_time(position)
                            with instruction_queue.mutex:
                                instruction_queue.queue.clear()
                            chunk = audio_streamer.get_next()
                            if chunk:
                                ws.send(wsMsg.binary(chunk))
                            else:
                                ws.send(wsMsg.text(json.dumps({
                                    "type": "song_end"
                                })))
                                audio_streamer = None
                                playing = False

                    elif inst.inst == "search_query":  # search completion
                        query = inst.params.get("query")
                        with Event_Handler.Lock:
                            songs = Event_Handler.db.search_close_songs(query)
                        ws.send(wsMsg.text(json.dumps({"type": "top_searches", "searches": ",".join(songs)})))

                    elif inst.inst == "search":
                        song_name = inst.params.get("song_name")
                        with Event_Handler.Lock:
                            song = Event_Handler.db.get_song_info_by_name(song_name)
                        if song:
                            with open(song.thumbnail_path, "rb") as f:
                                data = f.read()
                            b64_data = base64.b64encode(data).decode()
                            rel_date = song.release_date.isoformat() if hasattr(song.release_date,
                                                                                'isoformat') else str(song.release_date)

                            ws.send(wsMsg.text(json.dumps({
                                "type": "song_info",
                                "info": {
                                    "name": song.name,
                                    "artist": song.artist,
                                    "album": song.album,
                                    "release_date": rel_date,
                                    "likes_count": song.likes_count,
                                    "thumbnail": b64_data
                                }
                            })))
                        else:
                            songs = download_multiple(song_name)
                            ws.send(wsMsg.text(json.dumps({"type": "downloading"})))

                            for s in songs:
                                date_str = str(s["release_date"])
                                try:
                                    parsed_date = datetime.strptime(date_str, "%Y%m%d").date()
                                except ValueError:
                                    parsed_date = datetime(2000, 1, 1).date()
                                print("inserting song into database and sending...")
                                song = Song(0,
                                            s["title"],
                                            s["artist"],
                                            s["album"],
                                            parsed_date,
                                            0,
                                            s["audio_path"],
                                            s["thumbnail_path"])
                                with Event_Handler.Lock:
                                    Event_Handler.db.insert_song(song)
                                with open(song.thumbnail_path, "rb") as f:
                                    data = f.read()
                                b64_data = base64.b64encode(data).decode()
                                rel_date = song.release_date.isoformat() if hasattr(song.release_date,
                                                                                    'isoformat') else str(
                                    song.release_date)

                                ws.send(wsMsg.text(json.dumps({
                                    "type": "song_info",
                                    "info": {
                                        "name": song.name,
                                        "artist": song.artist,
                                        "album": song.album,
                                        "release_date": rel_date,
                                        "likes_count": song.likes_count,
                                        "thumbnail": b64_data
                                    }
                                })))

                    elif inst.inst == "get_top_songs":
                        with Event_Handler.Lock:
                            songs = Event_Handler.db.get_top_songs(20)
                            print(songs)
                            for song in songs:
                                if song:
                                    with open(song.thumbnail_path, "rb") as f:
                                        data = f.read()
                                    b64_data = base64.b64encode(data).decode()
                                    rel_date = song.release_date.isoformat() if hasattr(song.release_date,
                                                                                        'isoformat') else str(
                                        song.release_date)

                                    ws.send(wsMsg.text(json.dumps({
                                        "type": "song_info",
                                        "info": {
                                            "name": song.name,
                                            "artist": song.artist,
                                            "album": song.album,
                                            "release_date": rel_date,
                                            "likes_count": song.likes_count,
                                            "thumbnail": b64_data
                                        }
                                    })))

                    elif inst.inst == "need_chunk":
                        if audio_streamer and playing:
                            chunk = audio_streamer.get_next()

                            if chunk:
                                ws.send(wsMsg.binary(chunk))
                            else:
                                ws.send(wsMsg.text(json.dumps({
                                    "type": "song_end"
                                })))

                                audio_streamer = None
                                playing = False

                current_time = time.time()
                if audio_streamer and (current_time - last_state_update > 0.5):
                    ws.send(wsMsg.text(json.dumps({
                        "type": "state",
                        "playing": playing,
                        "position": str(audio_streamer.get_time()),
                    })))
                    last_state_update = current_time
            except Exception as e:
               print(e)
               break


if __name__ == '__main__':
    names = [
        "Blinding Lights",
        "Shape of You",
        "Someone Like You",
        "Rolling in the Deep",
        "Bohemian Rhapsody",
        "Billie Jean",
        "Bad Guy",
        "Stay",
        "As It Was",
        "Levitating",
        "Save Your Tears",
        "Shallow",
        "Uptown Funk",
        "Despacito",
        "Thinking Out Loud",
        "Perfect",
        "All of Me",
        "Hello",
        "Havana",
        "God's Plan",
        "Sunflower",
        "Old Town Road",
        "Rockstar",
        "Dance Monkey",
        "Believer",
        "Radioactive",
        "Counting Stars",
        "Roar",
        "Firework",
        "Dark Horse",
        "Halo",
        "Poker Face",
        "Bad Romance",
        "Viva La Vida",
        "Fix You",
        "Yellow",
        "Paradise",
        "The Scientist",
        "Clocks",
        "In the End",
        "Numb",
        "Crawling",
        "Smells Like Teen Spirit",
        "Wonderwall",
        "Sweet Child O' Mine",
        "Don't Stop Believin'",
        "Livin' on a Prayer",
        "Eye of the Tiger",
        "Beat It",
        "Thriller",
        "Like a Prayer",
        "Take On Me",
        "Africa",
        "Every Breath You Take",
        "With or Without You",
        "Where Is the Love?",
        "Mr. Brightside",
        "Seven Nation Army",
        "Somebody That I Used to Know",
        "Let Her Go",
        "Wake Me Up",
        "Titanium",
        "Animals",
        "Levels",
        "One Kiss",
        "Closer",
        "Don't Let Me Down",
        "Ride",
        "Stressed Out",
        "Heathens",
        "Lovely",
        "drivers license",
        "good 4 u",
        "traitor",
        "Peaches",
        "Watermelon Sugar",
        "Senorita",
        "Cheap Thrills",
        "Happy",
        "Just the Way You Are",
        "Grenade",
        "Locked Out of Heaven",
        "Starboy",
        "The Hills",
        "Can't Feel My Face",
        "In My Feelings",
        "Nice for What",
        "Work",
        "Rude",
        "Cheerleader",
        "Sugar",
        "Payphone",
        "Moves Like Jagger",
        "We Found Love",
        "Diamonds",
        "What Do You Mean?",
        "Sorry",
        "Intentions",
        "Peaches (feat. Daniel Caesar)",
        "As It Was (Harry Styles)"
    ]
    db = App_ORM()

    for name in names:
        s = download_multiple(name, limit=1)[0]
        date_str = str(s["release_date"])
        try:
            parsed_date = datetime.strptime(date_str, "%Y%m%d").date()
        except ValueError:
            parsed_date = datetime(2000, 1, 1).date()
        song = Song(0,
                    s["title"],
                    s["artist"],
                    s["album"],
                    parsed_date,
                    0,
                    s["audio_path"],
                    s["thumbnail_path"])
        print(song)
        db.insert_song(song)
        print("inserted")
