# Whisper Video Subtitles

Automatically generate and burn subtitles into videos using OpenAI Whisper.

## Example

```bash
python speech_to_text.py ./assets/Gnome_Interview_Video_on_Fox_News.mp4 --output ./assets/Gnome_Interview_Video_on_Fox_News_transcribed.mp4 --no-show
```

**Output:** Video with white text on black background at the bottom, synced to speech.

https://github.com/user-attachments/assets/40c16fbc-321d-46ff-aa07-1e6d7dfa78f7

*Subtitles appear automatically at the bottom with precise timing*

## Requirements

- Python 3.12+
- FFmpeg (must be installed and in PATH)
- Dependencies:
  ```bash
  pip install openai-whisper opencv-python
  ```

**Install FFmpeg:**
- Ubuntu: `sudo apt install ffmpeg`
- Mac: `brew install ffmpeg`
- Conda: `conda install -c conda-forge ffmpeg`

## Usage

### Input Formats

Supports both video and audio files:
- **Video:** `.mp4` and other FFmpeg-supported formats
- **Audio:** `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.aac`, `.wma`

### Output Formats

Output format is determined by the file extension:
- **`.mp4`** (or other video) - Video with burned-in subtitles
- **`.srt`** - SRT subtitle file with timestamps
- **`.txt`** - Raw tokens with Whisper special tokens (e.g., `<|startoftranscript|><|en|>...`)

---

### Video Input Examples

**Live preview (no output file):**
```bash
python speech_to_text.py input.mp4
```

**Save video with burned subtitles:**
```bash
python speech_to_text.py input.mp4 -o output.mp4
```

**Export SRT subtitles only (no video processing):**
```bash
python speech_to_text.py input.mp4 -o subtitles.srt
```

**Export raw tokens with special markers:**
```bash
python speech_to_text.py input.mp4 -o transcription.txt
```

Output format:
```
<|startoftranscript|><|en|><|transcribe|><|0.00|> Hello world...<|endoftranscript|>
```

**Compress output video (smaller file, slower):**
```bash
python speech_to_text.py input.mp4 -o output.mp4 --compress
```

**No live preview (faster processing):**
```bash
python speech_to_text.py input.mp4 -o output.mp4 --no-show
```

---

### Audio Input Examples

**Transcribe audio to SRT:**
```bash
python speech_to_text.py input.mp3 -o subtitles.srt
```

**Transcribe audio to raw tokens:**
```bash
python speech_to_text.py input.mp3 -o transcription.txt
```

**Default output (SRT with same name as input):**
```bash
python speech_to_text.py input.mp3
# Creates input.srt
```

---

### Model Selection

```bash
python speech_to_text.py input.mp4 --model small
```

Models: `tiny`, `base`, `small`, `medium`, `large` (larger = more accurate but slower)

---

### Language Options

**Specify source language:**
```bash
python speech_to_text.py input.mp4 --language en -o output.srt
python speech_to_text.py input.mp4 --language az -o output.srt
python speech_to_text.py input.mp4 --language ru -o output.srt
```

**Translate to English:**
```bash
python speech_to_text.py spanish_video.mp4 --translate -o english_subtitles.srt
python speech_to_text.py french_audio.mp3 --translate -o english.txt
```

---

### Combined Examples

**Full pipeline: video with subtitles, compressed, no preview:**
```bash
python speech_to_text.py input.mp4 -o output.mp4 --compress --no-show --model medium
```

**Translate foreign video and export SRT:**
```bash
python speech_to_text.py foreign_video.mp4 --translate --language es -o english_subs.srt
```

**High-accuracy transcription to raw tokens:**
```bash
python speech_to_text.py podcast.mp3 --model large -o transcript.txt
```

## Notes

- First run downloads the Whisper model (~140MB for base)
- Headless environments automatically disable preview
- Press 'q' during preview to quit
- Final output includes original audio
