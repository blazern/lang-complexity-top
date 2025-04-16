import argparse
import yt_dlp
import re
import logging
from pathlib import Path
import yaml
import sys

from yt_structs import YTVideo, YTChannel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description="Extract URLs of YouTube videos using yt_dlp")
    parser.add_argument("--channel-url", required=True)
    parser.add_argument("--title-regex", default=".*")
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    title_pattern = re.compile(args.title_regex)

    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_channels = []
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f) or {}
                existing_channels = data.get("channels", [])
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML: {e}")
                sys.exit(1)

        for ch in existing_channels:
            if ch.get("url") == args.channel_url:
                logger.error("Channel already exists in output file. Aborting.")
                sys.exit(1)

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(args.channel_url, download=False)
        videos = extract_yt_videos_from(info, title_pattern)
        channel = YTChannel(info['title'], args.channel_url, videos)

    existing_channels.append(channel.to_dict())
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump({"channels": existing_channels}, f, allow_unicode=True)

def extract_yt_videos_from(entry, title_pattern) -> set[YTVideo]:
    result = set()
    if 'url' in entry:
        if entry.get("title"):
            if title_pattern.match(entry["title"]):
                video = YTVideo(
                    entry["url"],
                    entry["title"],
                    title_pattern.pattern,
                )
                result.add(video)
        else:
            logger.warning(f"No title in entry: {entry}")
    if "entries" in entry:
        for e in entry["entries"]:
            result.update(extract_yt_videos_from(e, title_pattern))
    return result

if __name__ == '__main__':
    main()


# channel_url = 'https://www.youtube.com/@MrWissen2go/'  # or /@username or /channel/ID

# ydl_opts = {
#     'extract_flat': True,  # Don't download videos, just extract metadata
#     'quiet': True,
# }

# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     info = ydl.extract_info(channel_url, download=False)
#     for entry in info['entries']:
#         if 'url' in entry:
#             breakpoint()
#             print(entry['url'])  # or entry['title'], etc.
#         if 'entries' in entry:
#             for entry in entry['entries']:
#                 breakpoint()
#                 print(entry['url'])  # or entry['title'], etc.




# import whisper

# model = whisper.load_model("small")
# result = model.transcribe("audio2.mp3", language="de")
# text = result["text"]
# print(text)




# for sent in doc.sents:
#     print("----")
#     print(sentence)



# avg_sentence_length = sum(len(sent) for sent in doc.sents) / len(list(doc.sents))
# words = [token.text for token in doc if token.is_alpha]
# avg_word_length = sum(len(w) for w in words) / len(words)
# sub_conjs = [token for token in doc if token.pos_ == "SCONJ"]
# print("Subordinating conjunctions:", len(sub_conjs))
# print("Named entities:", len(doc.ents))
# complexity_score = (avg_sentence_length * 0.4) + (avg_word_length * 0.3) + (len(sub_conjs) * 0.3)
# print(f"complexity_score: {complexity_score}")

# # complexity_score: 6.851006063947079
# # complexity_score: 6.851006063947079




# from __future__ import unicode_literals
# import yt_dlp


# ydl_opts = {
#     'format': 'bestaudio/best',
#     'postprocessors': [{
#         'key': 'FFmpegExtractAudio',
#         'preferredcodec': 'mp3',
#         'preferredquality': '192',
#     }],
# }
# with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#     ydl.download(['https://www.youtube.com/watch?v=gIusDqd9y2Y'])



# # with yt_dlp.YoutubeDL({}) as ydl:
# #     ydl.download(['https://www.youtube.com/watch?v=stcXXZ-4SD0'])
