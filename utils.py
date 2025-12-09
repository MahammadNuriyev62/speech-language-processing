import os
import sys
import shutil


def check_ffmpeg():
    """
    Checks if ffmpeg is installed and available in the system PATH.
    """
    if not shutil.which("ffmpeg"):
        print("Error: 'ffmpeg' is not installed or not found in PATH.")
        print("Whisper requires ffmpeg for audio processing.")
        print("\nTo fix this:")
        print("  - If using Conda:  conda install -c conda-forge ffmpeg")
        print("  - If on Ubuntu:    sudo apt install ffmpeg")
        print("  - If on Mac:       brew install ffmpeg")
        sys.exit(1)


def is_headless():
    """
    Detects if the environment is headless (no display).
    """
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in os.environ:
            return True
    return False


def is_audio_only(file_path):
    """
    Checks if the file is an audio-only format (no video stream).
    """
    audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma'}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in audio_extensions


def get_output_format(output_path):
    """
    Determines output format based on file extension.
    Returns: 'srt', 'txt', or 'video'
    """
    if not output_path:
        return None
    ext = os.path.splitext(output_path)[1].lower()
    if ext == '.srt':
        return 'srt'
    elif ext == '.txt':
        return 'txt'
    else:
        return 'video'
