import os
import sys
import warnings

import whisper

from cli import parse_arguments
from utils import check_ffmpeg, is_headless, is_audio_only, get_output_format
from output import write_srt, write_raw_tokens
from video import process_video

# Suppress the noisy NumPy version warning from SciPy
warnings.filterwarnings("ignore", category=UserWarning, module='scipy')


def main():
    args = parse_arguments()

    # 0. Check Dependencies
    check_ffmpeg()

    # 1. Validation
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    # 2. Check if input is audio-only
    audio_only = is_audio_only(args.input_file)
    if audio_only:
        print(f"Detected audio-only file: {args.input_file}")

    # 3. Auto-detect Headless Environment (only relevant for video files)
    if not audio_only and is_headless():
        if not args.no_show:
            print("\nWARNING: No display detected (Headless environment).")
            print("         Disabling live window to prevent crashes.")
            args.no_show = True

        if not args.output:
            print("         WARNING: You are in headless mode but didn't specify an output file.")
            print("         The script will run but you won't see the result.")
            print("         Use -o output.mp4 to save the result.\n")

    # 4. Load Whisper Model
    print(f"Loading Whisper model ('{args.model}')...")
    model = whisper.load_model(args.model)

    # 5. Transcribe (or Translate)
    task = "translate" if args.translate else "transcribe"
    if args.translate:
        print("Translating audio to English... (This may take some time)")
    else:
        print("Transcribing audio... (This may take some time)")

    # We use fp16=False to avoid warnings if you are on a CPU
    transcribe_options = {"fp16": False, "task": task}
    if args.language:
        transcribe_options["language"] = args.language
        print(f"Source language: {args.language}")
    result = model.transcribe(args.input_file, **transcribe_options)
    print(f"Detected/used language: {result['language']}")
    if args.translate:
        print("Translated to: English")
    segments = result["segments"]
    print("Transcription complete.")

    # 6. Determine output format and handle accordingly
    output_format = get_output_format(args.output)

    # Handle text-based outputs (SRT or raw tokens)
    if output_format in ('srt', 'txt'):
        if output_format == 'srt':
            write_srt(segments, args.output)
            print(f"Subtitles saved to: {args.output}")
        else:  # txt - raw tokens
            write_raw_tokens(result, args.output, task=task)
            print(f"Raw tokens saved to: {args.output}")
        print("Done.")
        return

    # Handle audio-only files (default to SRT if no output specified)
    if audio_only:
        if args.output:
            output_path = args.output
            # Ensure .srt extension for audio files
            if not output_path.lower().endswith('.srt'):
                output_path = os.path.splitext(output_path)[0] + '.srt'
        else:
            # Default output name based on input
            output_path = os.path.splitext(args.input_file)[0] + '.srt'

        write_srt(segments, output_path)
        print(f"Subtitles saved to: {output_path}")
        print("Done.")
        return

    # 7. Process video files
    process_video(
        input_file=args.input_file,
        output_path=args.output,
        segments=segments,
        no_show=args.no_show,
        compress=args.compress
    )

    print("Done.")


if __name__ == "__main__":
    main()
