def format_timestamp_srt(seconds):
    """
    Converts seconds to SRT timestamp format: HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(segments, output_path):
    """
    Writes transcription segments to an SRT subtitle file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start = format_timestamp_srt(seg['start'])
            end = format_timestamp_srt(seg['end'])
            text = seg['text'].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")


def write_raw_tokens(result, output_path, task="transcribe"):
    """
    Writes raw tokens with Whisper special tokens visible to a text file.
    Format: <|startoftranscript|><|en|><|transcribe|><|0.00|>Hello world<|2.50|>...<|endoftranscript|>
    """
    lang = result['language']
    segments = result['segments']

    # Build token string with special tokens
    output = f"<|startoftranscript|><|{lang}|><|{task}|>"

    for seg in segments:
        # Add timestamp token for segment start
        start_time = seg['start']
        output += f"<|{start_time:.2f}|>"
        # Add the transcribed text
        output += seg['text']

    output += "<|endoftranscript|>"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
