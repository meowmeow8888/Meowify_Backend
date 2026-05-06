import base64
import json
import threading

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
                        ws.send(wsMsg.text({"type": "song_start"}))

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
                            audio_streamer.jump_to_time(position)

                    elif inst.inst == "search_query": # search completion
                        query = inst.params.get("query")
                        with Event_Handler.Lock:
                            songs = Event_Handler.db.search_close_songs(query)
                        ws.send(wsMsg.text({"type": "top_searches", "searches": ",".join(songs)}))

                    elif inst.inst == "search":
                        song_name = inst.params.get("song_name")
                        with Event_Handler.Lock:
                            song = Event_Handler.db.get_song_info_by_name(song_name)
                        if song:
                            with open(song.thumbnail_path, "rb") as f:
                                data = f.read()
                            enc_data = base64.b64encode(data)
                            ws.send(wsMsg.text({
                                "type": "song_info",
                                "info" : {
                                    "name" : song.name,
                                    "artist" : song.artist,
                                    "album" : song.album,
                                    "release_date" : song.release_date,
                                    "likes_count": song.likes_count,
                                    "thumbnail": enc_data
                                }
                            }))
                        else:
                            download_multiple(song_name)
                            ws.send(wsMsg.text({"type": "downloading"}))

            except Exception as e:
                print(e)

            if audio_streamer and playing:
                chunk = audio_streamer.get_next()

                if chunk:
                    ws.send(wsMsg.binary(chunk).to_bytes())
                else:
                    ws.send(wsMsg.text(json.dumps({
                        "type": "song_end"
                    })).to_bytes())

                    audio_streamer = None
                    playing = False

            if audio_streamer:
                ws.send(wsMsg.text(json.dumps({
                    "type": "state",
                    "playing": playing,
                    "position": str(audio_streamer.get_time()),
                })).to_bytes())