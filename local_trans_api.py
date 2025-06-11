import os
import time
from pathlib import Path

from openai import OpenAI
from pydub import AudioSegment

from video_funcs import extract_audio_from_video, format_time

# Directories for processing files
video_dir = r"C:\Whisper\usalaia"
audios_dir = r"C:\Whisper\usalaia"
transcriptions_dir = r"C:\Whisper\usalaia"
srt_dir = r"C:\Whisper\usalaia"

# File formats
audio_format = ".mp3"
output_format = "txt"
video_format = ".mp4"

# Model and languages
models = ["whisper-1"]
langs = ["en", "es"]

MAX_CHARS_PER_SUBTITLE = 130

client = OpenAI()  # Requires OPENAI_API_KEY env var


def transcribe_audio_api(file_path: str, model_name: str, lang: str) -> dict:
    """Send the file to the OpenAI API and return the verbose JSON result."""
    with open(file_path, "rb") as f:
        start_time = time.time()
        resp = client.audio.transcriptions.create(
            file=f,
            model=model_name,
            language=lang,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
        end_time = time.time()
    result = resp.model_dump()
    result["processing_time"] = end_time - start_time
    return result


def save_transcription(result: dict, file_path: str, model_name: str, lang: str) -> None:
    base = Path(file_path).stem
    audio = AudioSegment.from_file(file_path)
    length = len(audio) / 1000
    info = (
        f"Model: {model_name}\n"
        f"Processing Time: {result['processing_time']} seconds\n"
        f"Audio Length: {length} seconds\n\n"
        f"{result['text']}"
    )
    out_path = Path(transcriptions_dir) / f"{base}_{model_name}_{lang}.{output_format}"
    out_path.write_text(info, encoding="utf-8")


def save_srt(result: dict, file_path: str, model_name: str, lang: str) -> None:
    if not srt_dir:
        return

    base = Path(file_path).stem
    srt_path = Path(srt_dir) / f"{base}_{model_name}_{lang}.srt"
    subtitle_index = 1

    with srt_path.open("w", encoding="utf-8") as srt_file:
        for segment in result.get("segments", []):
            words = segment.get("words", [])
            if not words:
                start_t = segment["start"]
                end_t = segment["end"]
                text = segment["text"].strip()
                words_split = text.split()
                current = ""
                subs = []
                for word in words_split:
                    if len(current) + len(word) + 1 > MAX_CHARS_PER_SUBTITLE:
                        subs.append(current.strip())
                        current = word + " "
                    else:
                        current += word + " "
                if current.strip():
                    subs.append(current.strip())
                num = len(subs)
                duration = end_t - start_t
                for i, subtext in enumerate(subs):
                    start = start_t + (duration / num) * i
                    end = start + duration / num
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
                    srt_file.write(f"{subtext}\n\n")
                    subtitle_index += 1
                continue

            current = ""
            start_sub = words[0]["start"]
            for word_info in words:
                word = word_info["word"]
                if len(current) + len(word) + 1 > MAX_CHARS_PER_SUBTITLE:
                    end_sub = word_info["start"]
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{format_time(start_sub)} --> {format_time(end_sub)}\n")
                    srt_file.write(f"{current.strip()}\n\n")
                    subtitle_index += 1
                    current = word + " "
                    start_sub = word_info["start"]
                else:
                    current += word + " "
            if current.strip():
                end_sub = words[-1]["end"]
                srt_file.write(f"{subtitle_index}\n")
                srt_file.write(f"{format_time(start_sub)} --> {format_time(end_sub)}\n")
                srt_file.write(f"{current.strip()}\n\n")
                subtitle_index += 1


def process_file(file_path: str, model_name: str, lang: str) -> None:
    result = transcribe_audio_api(file_path, model_name, lang)
    save_transcription(result, file_path, model_name, lang)
    save_srt(result, file_path, model_name, lang)


if __name__ == "__main__":
    Path(audios_dir).mkdir(parents=True, exist_ok=True)
    Path(transcriptions_dir).mkdir(parents=True, exist_ok=True)
    if srt_dir:
        Path(srt_dir).mkdir(parents=True, exist_ok=True)

    for model_name in models:
        source_dir = video_dir if video_dir and os.path.exists(video_dir) else audios_dir
        file_ext = video_format if source_dir == video_dir else audio_format
        for file in os.listdir(source_dir):
            if file.endswith(file_ext):
                path = os.path.join(source_dir, file)
                if source_dir == video_dir:
                    path = extract_audio_from_video(path, audios_dir)
                for lang in langs:
                    process_file(path, model_name, lang)
