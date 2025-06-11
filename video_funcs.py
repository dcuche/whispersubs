import subprocess
from os import path

import subprocess
from pathlib import Path

def extract_audio_from_video(
    video_file_path: str | Path,
    audios_dir: str | Path,
    extracted_audio_ext: str = ".mp3",
    bitrate: str = "64k",
    sample_rate: int = 44100,
    channels: int = 1,
    overwrite: bool = False,
) -> str:
    video_file_path = Path(video_file_path)
    audios_dir      = Path(audios_dir)
    audios_dir.mkdir(parents=True, exist_ok=True)

    base_name = video_file_path.stem
    out_path  = audios_dir / f"{base_name}{extracted_audio_ext}"

    if out_path.exists() and not overwrite:
        return str(out_path)

    # Pick the right codec for the chosen extension
    if extracted_audio_ext.lower() == ".mp3":
        codec_args = ["-c:a", "libmp3lame", "-b:a", bitrate]
    elif extracted_audio_ext.lower() == ".wav":
        codec_args = ["-c:a", "pcm_s16le"]
    else:
        raise ValueError(f"Unsupported audio extension: {extracted_audio_ext}")

    cmd = [
        "ffmpeg",
        "-y" if overwrite else "-n",   # overwrite or fail if file exists
        "-i", str(video_file_path),
        "-vn",                        # no video
        "-ar", str(sample_rate),
        "-ac", str(channels),
        *codec_args,
        str(out_path),
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed:\nSTDOUT:\n{result.stdout.decode()}\n"
            f"STDERR:\n{result.stderr.decode()}"
        )

    return str(out_path)


def extract_audio_from_video_old(video_file_path, audios_dir, extracted_audio_ext=".wav"):
	base_filename = path.splitext(path.basename(video_file_path))[0]
	extracted_audio_path = path.join(audios_dir, f"{base_filename}{extracted_audio_ext}")
	if not path.exists(extracted_audio_path):
		command = ["ffmpeg", "-i", video_file_path, "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", extracted_audio_path]
		subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	return extracted_audio_path

def format_time(seconds):
	hours = int(seconds // 3600)
	minutes = int((seconds % 3600) // 60)
	seconds = seconds % 60
	return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')