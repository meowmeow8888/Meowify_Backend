from pathlib import Path
import yt_dlp


def download_multiple(song_name, limit=3):
    base_dir = Path(__file__).resolve().parent

    songs_path = (base_dir / "../saves/songs").resolve()
    thumbs_path = (base_dir / "../saves/thumbnails").resolve()

    songs_path.mkdir(parents=True, exist_ok=True)
    thumbs_path.mkdir(parents=True, exist_ok=True)

    query = f"ytsearch{limit}:{song_name}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'skip_unavailable_fragments': True,
        'ignoreerrors': True,
        'match_filter': lambda info: None if info.get('duration') and info['duration'] <= 600 else 'too long',
        'outtmpl': {
            'default': str(songs_path / '%(title)s-%(id)s.%(ext)s'),
            'thumbnail': str(thumbs_path / '%(title)s-%(id)s.%(ext)s'),
        },
        'writethumbnail': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            }],
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)

        entries = info.get('entries', []) if 'entries' in info else [info]

        for entry in entries:
            title = entry.get("title")
            vid_id = entry.get("id")

            audio_path = songs_path / f"{title}-{vid_id}.mp3"
            thumb_path = thumbs_path / f"{title}-{vid_id}.jpg"

            results.append({
                "title": title,
                "artist": entry.get("artist") or entry.get("uploader"),
                "album": entry.get("album"),
                "release_date": entry.get("release_date") or entry.get("upload_date"),
                "audio_path": str(audio_path),
                "thumbnail_path": str(thumb_path),
            })

    return results


if __name__ == '__main__':
    data = download_multiple("The Great Divide")
    for song in data:
        print(song)
