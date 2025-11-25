# Whisper Video Subtitles

Automatically generate and burn subtitles into videos using OpenAI Whisper.

## Example

```bash
python main.py ./assets/Gnome_Interview_Video_on_Fox_News.mp4 --output ./assets/Gnome_Interview_Video_on_Fox_News_transcribed.mp4 --no-show
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

**Basic (live preview):**
```bash
python whisper_subtitles.py input.mp4
```

**Save output:**
```bash
python whisper_subtitles.py input.mp4 -o output.mp4
```

**Compress output (smaller file size):**
```bash
python whisper_subtitles.py input.mp4 -o output.mp4 --compress
```

**No preview (faster):**
```bash
python whisper_subtitles.py input.mp4 -o output.mp4 --no-show
```

**Choose model:**
```bash
python whisper_subtitles.py input.mp4 --model small
```

Models: `tiny`, `base`, `small`, `medium`, `large` (larger = more accurate but slower)

## Notes

- First run downloads the Whisper model (~140MB for base)
- Headless environments automatically disable preview
- Press 'q' during preview to quit
- Final output includes original audio
