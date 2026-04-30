from pathlib import Path
import yt_dlp


def download_multiple(song_name, limit=3):
    base_dir = Path(__file__).resolve().parent

    songs_path = (base_dir / "../downloads/songs").resolve()
    thumbs_path = (base_dir / "../downloads/thumbnails").resolve()

    songs_path.mkdir(parents=True, exist_ok=True)
    thumbs_path.mkdir(parents=True, exist_ok=True)

    query = f"ytsearch{limit}:{song_name}"

    ydl_opts = {
        'format': 'bestaudio/best',

        'outtmpl': {
            'default': str(songs_path / '%(title)s-%(id)s.%(ext)s'),
            'thumbnail': str(thumbs_path / '%(title)s-%(id)s.%(ext)s'),
        },
        'writethumbnail': True,

        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],

    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])


if __name__ == '__main__':
    download_multiple("The Great Divide")
