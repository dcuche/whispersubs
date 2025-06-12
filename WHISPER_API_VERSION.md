The OpenAI Speech-to-Text API currently offers three models for transcription:
- `whisper-1` (based on the open source Whisper V2 model)
- `gpt-4o-transcribe`
- `gpt-4o-mini-transcribe`

When requesting word-level timestamps you must set `response_format="verbose_json"`
and pass `timestamp_granularities=["word"]`.
