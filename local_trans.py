import os
import whisper
import time
from video_funcs import extract_audio_from_video, format_time
from pydub import AudioSegment
import warnings
warnings.filterwarnings("ignore", message="Failed to launch Triton kernels.*")


video_dir = r"C:\Whisper\usalaia"
audios_dir = r"C:\Whisper\usalaia"
transcriptions_dir = r"C:\Whisper\usalaia"
srt_dir = r"C:\Whisper\usalaia"
audio_format = ".mp3"
output_format = "txt"
video_format = ".mp4"

models = ['medium']
langs = ['en','es']

MAX_CHARS_PER_SUBTITLE = 130  # Maximum characters per subtitle

def transcribe_audio(file_path, model, model_name, transcriptions_dir, srt_dir=None, lang='en'):
    print(f"Transcribing {os.path.basename(file_path)} using model {model_name}")
    start_time = time.time()
    result = model.transcribe(
        file_path,
        language=lang,
        word_timestamps=True,  # Enable word-level timestamps
        verbose=False
    )
    end_time = time.time()

    base_filename = os.path.splitext(os.path.basename(file_path))[0]
    processing_time = end_time - start_time

    audio = AudioSegment.from_file(file_path)
    audio_length = len(audio) / 1000

    transcription_info = f"Model: {model_name}\nProcessing Time: {processing_time} seconds\nAudio Length: {audio_length} seconds\n\n{result['text']}"
    output_path = os.path.join(transcriptions_dir, f"{base_filename}_{model_name}.{output_format}")
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(transcription_info)

    if srt_dir:
        srt_path = os.path.join(srt_dir, f"{base_filename}_{model_name}_{lang}.srt")
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            subtitle_index = 1
            MAX_CHARS_PER_SUBTITLE = 80  # Maximum characters per subtitle
            for segment in result["segments"]:
                words = segment.get("words", [])
                if not words:
                    # Handle empty words list
                    print(f"Warning: No word timestamps for segment starting at {segment['start']}s")
                    # Option 1: Skip the segment
                    # continue

                    # Option 2: Use segment start and end times and segment text
                    start_time_subtitle = segment["start"]
                    end_time_subtitle = segment["end"]
                    text = segment["text"].strip()

                    # Split the text into subtitles based on character limit
                    words_in_text = text.split()
                    current_subtitle = ""
                    subtitles = []
                    for word in words_in_text:
                        if len(current_subtitle) + len(word) + 1 > MAX_CHARS_PER_SUBTITLE:
                            subtitles.append(current_subtitle.strip())
                            current_subtitle = word + " "
                        else:
                            current_subtitle += word + " "
                    if current_subtitle.strip():
                        subtitles.append(current_subtitle.strip())

                    # Distribute time evenly among the subtitles
                    num_subtitles = len(subtitles)
                    duration = end_time_subtitle - start_time_subtitle
                    for i, subtitle_text in enumerate(subtitles):
                        start = start_time_subtitle + (duration / num_subtitles) * i
                        end = start + (duration / num_subtitles)
                        srt_file.write(f"{subtitle_index}\n")
                        srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
                        srt_file.write(f"{subtitle_text}\n\n")
                        subtitle_index += 1
                    continue  # Move to the next segment

                # Proceed with word-level timestamp processing
                current_subtitle = ""
                start_time_subtitle = words[0]["start"]
                for word_info in words:
                    word = word_info["word"]
                    if len(current_subtitle) + len(word) + 1 > MAX_CHARS_PER_SUBTITLE:
                        # Write the current subtitle to the SRT file
                        end_time_subtitle = word_info["start"]
                        srt_file.write(f"{subtitle_index}\n")
                        srt_file.write(f"{format_time(start_time_subtitle)} --> {format_time(end_time_subtitle)}\n")
                        srt_file.write(f"{current_subtitle.strip()}\n\n")
                        subtitle_index += 1
                        # Start a new subtitle
                        current_subtitle = word + " "
                        start_time_subtitle = word_info["start"]
                    else:
                        current_subtitle += word + " "
                # Write any remaining subtitle
                if current_subtitle.strip():
                    end_time_subtitle = words[-1]["end"]
                    srt_file.write(f"{subtitle_index}\n")
                    srt_file.write(f"{format_time(start_time_subtitle)} --> {format_time(end_time_subtitle)}\n")
                    srt_file.write(f"{current_subtitle.strip()}\n\n")
                    subtitle_index += 1



os.makedirs(audios_dir, exist_ok=True)
os.makedirs(transcriptions_dir, exist_ok=True)
if srt_dir:
	os.makedirs(srt_dir, exist_ok=True)

for model_name in models:
	model = whisper.load_model(model_name)
	source_dir = video_dir if video_dir and os.path.exists(video_dir) else audios_dir
	file_extension = video_format if source_dir == video_dir else audio_format

	for file in os.listdir(source_dir):
		if file.endswith(file_extension):
			file_path = os.path.join(source_dir, file)
			if source_dir == video_dir:
				file_path = extract_audio_from_video(file_path, audios_dir)
			for lang in langs:
				transcribe_audio(file_path, model, model_name, transcriptions_dir, srt_dir, lang)
