from pathlib import Path
import yt_dlp


def download_multiple(song_name, limit=3):
    base_dir = Path(__file__).resolve().parent

    songs_path = (base_dir / "../saves/songs").resolve()
    thumbs_path = (base_dir / "../saves/thumbnails").resolve()

    songs_path.mkdir(parents=True, exist_ok=True)
    thumbs_path.mkdir(parents=True, exist_ok=True)

    search_query = f"ytsearch{limit + 5}:{song_name}"

    search_opts = {
        'extract_flat': True,
        'quiet': True,
    }

    valid_urls = []

    with yt_dlp.YoutubeDL(search_opts) as ydl:
        search_info = ydl.extract_info(search_query, download=False)
        entries = search_info.get('entries', [])

        for entry in entries:
            url = entry.get('url', '')
            duration = entry.get('duration')

            if any(kw in url for kw in ['/channel/', '/c/', '/user/', '/@', 'playlist?']):
                continue

            if not duration or duration > 600:
                continue

            valid_urls.append(url)

            if len(valid_urls) == limit:
                break

    if not valid_urls:
        return []

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
        for url in valid_urls:
            info = ydl.extract_info(url, download=True)

            if not info:
                continue

            title = info.get("title")
            vid_id = info.get("id")

            audio_path = songs_path / f"{title}-{vid_id}.mp3"
            thumb_path = thumbs_path / f"{title}-{vid_id}.jpg"

            results.append({
                "title": title,
                "artist": info.get("artist") or info.get("uploader"),
                "album": info.get("album"),
                "release_date": info.get("release_date") or info.get("upload_date"),
                "audio_path": str(audio_path),
                "thumbnail_path": str(thumb_path),
            })

    return results


if __name__ == '__main__':
    data = download_multiple("The Great Divide")
    for song in data:
        print(song)