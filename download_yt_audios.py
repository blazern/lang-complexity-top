import argparse
import yaml
import logging
import re
import random
import time
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_structs import YTChannel, YTVideo
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def sanitize_name(name: str) -> str:
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-zA-Z0-9_-]", "", name)
    return name.lower()

def load_channels_from_yaml(path: Path) -> list[YTChannel]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    channels = []
    for ch in data.get("channels", []):
        videos = {YTVideo(**v) for v in ch["videos"]}
        channels.append(YTChannel(ch["title"], ch["url"], videos))
    return channels

def download_audio(url: str, out_path: Path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(out_path),
        'quiet': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    parser = argparse.ArgumentParser(description="Download audio from YouTube channels in round-robin order.")
    parser.add_argument("--input-file", required=True, help="YAML file from the extractor script.")
    parser.add_argument("--output-dir", required=True, help="Directory to store downloaded audios.")
    parser.add_argument("--min-wait", type=int, default=10, help="Minimum wait time in seconds between downloads.")
    parser.add_argument("--max-wait", type=int, default=60, help="Maximum wait time in seconds between downloads.")
    parser.add_argument("--only-channels", nargs='*', help="List of channel names to include. Others will be ignored.")
    args = parser.parse_args()

    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    channels = load_channels_from_yaml(input_file)

    # Filter by channel names if requested
    if args.only_channels:
        wanted = {sanitize_name(name) for name in args.only_channels}
        channels = [ch for ch in channels if sanitize_name(ch.title) in wanted]
        if not channels:
            logger.info("No matching channels found based on names.")
            return
        logger.info(f"Filtering: Using only {len(channels)} channel(s).")

    videos_to_download = []
    already_downloaded = 0

    for ch in channels:
        safe_channel_name = sanitize_name(ch.title)
        channel_folder = output_dir / safe_channel_name
        for video in ch.videos:
            safe_video_title = sanitize_name(video.title)
            base_audio_path = channel_folder / safe_video_title
            existing_files = list(base_audio_path.parent.glob(f"{base_audio_path.name}.*"))
            if existing_files:
                already_downloaded += 1
            else:
                videos_to_download.append((ch, video))

    total_to_download = len(videos_to_download)
    logger.info(f"{already_downloaded} already downloaded, {total_to_download} to download.")

    if total_to_download == 0:
        logger.info("No new videos to download. Exiting.")
        return

    videos_by_channel = {}
    channel_lookup = {}

    for ch, video in videos_to_download:
        ch_key = sanitize_name(ch.title)
        channel_lookup[ch_key] = ch
        videos_by_channel.setdefault(ch_key, []).append(video)

    channel_keys = list(videos_by_channel.keys())
    current_index = 0
    downloaded = 0

    pbar = tqdm(total=total_to_download, desc=f"Downloaded: 0 / {total_to_download}", unit="audio")

    while any(videos_by_channel.values()):
        ch_key = channel_keys[current_index % len(channel_keys)]
        current_index += 1

        if not videos_by_channel[ch_key]:
            continue

        video = videos_by_channel[ch_key].pop(0)
        ch = channel_lookup[ch_key]

        safe_channel_name = sanitize_name(ch.title)
        safe_video_title = sanitize_name(video.title)
        channel_folder = output_dir / safe_channel_name
        channel_folder.mkdir(parents=True, exist_ok=True)

        audio_path = channel_folder / f"{safe_video_title}"
        try:
            download_audio(video.url, audio_path)
            downloaded += 1
        except Exception as e:
            logger.error(f"Failed to download {video.url}: {e}")
            continue

        pbar.update(1)
        pbar.set_description(f"Downloaded: {downloaded} / {total_to_download}")

        wait_time = random.randint(args.min_wait, args.max_wait)
        logger.info(f"Waiting {wait_time} seconds before next download...")
        time.sleep(wait_time)

    pbar.close()
    logger.info(f"\n✅ Done! Downloaded: {downloaded} | Skipped (pre-existing): {already_downloaded}")

if __name__ == "__main__":
    main()
