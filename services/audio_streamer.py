from pathlib import Path


class AudioStreamer:
    songs_path = (Path(__file__).resolve().parent / "../saves/songs").resolve()
    chunk_size = 32 * 1024

    def __init__(self, file_name):
        self.file_path = self.songs_path / file_name
        self.file = None
        self.offset = 0

    def _open(self):
        if self.file:
            self.file.close()
        self.file = open(self.file_path, "rb")

    def _sync_to_frame(self):
        while True:
            byte = self.file.read(1)
            if not byte:
                return None

            if byte[0] == 0xFF:
                next_byte = self.file.read(1)
                if next_byte and (next_byte[0] & 0xE0) == 0xE0:
                    self.file.seek(-2, 1)
                    return self.file.tell()
                else:
                    self.file.seek(-1, 1)

    def get_next(self):
        self._open()
        self.file.seek(self.offset)
        data = self.file.read(self.chunk_size)

        if not data:
            return None

        self.offset += len(data)
        self.file.close()
        return data

    def jump_to_byte(self, byte_offset):
        self.offset = max(0, byte_offset)
        self._open()
        self.file.seek(self.offset)
        self.offset = self._sync_to_frame()
        self.file.close()

    def jump_to_time(self, seconds, bitrate_kbps=128):
        byte_offset = int((bitrate_kbps * 1000 / 8) * seconds)
        self.jump_to_byte(byte_offset)
