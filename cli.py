import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate subtitles for a video or audio file using OpenAI Whisper."
    )

    # Input file (Required)
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input video or audio file (mp4, mp3, wav, etc.)."
    )

    # Output file (Optional)
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Path to save the output (video with subtitles for video input, SRT file for audio input)."
    )

    # Flag to hide the live window (Optional)
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not show the video window live (faster processing)."
    )

    # Model selection (Optional)
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size."
    )

    # Compression flag (Optional)
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress output video significantly (reduces file size, slower processing)."
    )

    # Language (Optional)
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language code for transcription (e.g., 'en', 'az', 'ru'). Auto-detects if not specified."
    )

    # Translate to English (Optional)
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Translate speech to English (instead of transcribing in original language)."
    )

    return parser.parse_args()
