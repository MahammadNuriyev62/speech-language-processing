import whisper
import cv2
import sys
import argparse
import time
import os
import shutil
import warnings
import subprocess

# Suppress the noisy NumPy version warning from SciPy
warnings.filterwarnings("ignore", category=UserWarning, module='scipy')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate subtitles for a video or audio file using OpenAI Whisper.")

    # Input file (Required)
    parser.add_argument("input_file", type=str, help="Path to the input video or audio file (mp4, mp3, wav, etc.).")
    
    # Output file (Optional)
    parser.add_argument("-o", "--output", type=str, help="Path to save the output (video with subtitles for video input, SRT file for audio input).")
    
    # Flag to hide the live window (Optional)
    parser.add_argument("--no-show", action="store_true", help="Do not show the video window live (faster processing).")
    
    # Model selection (Optional)
    parser.add_argument("--model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model size.")
    
    # Compression flag (Optional)
    parser.add_argument("--compress", action="store_true", help="Compress output video significantly (reduces file size, slower processing).")

    # Language (Optional)
    parser.add_argument("--language", type=str, default=None, help="Language code for transcription (e.g., 'en', 'az', 'ru'). Auto-detects if not specified.")

    # Translate to English (Optional)
    parser.add_argument("--translate", action="store_true", help="Translate speech to English (instead of transcribing in original language).")

    return parser.parse_args()

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

def draw_subtitle(frame, text):
    """
    Helper function to draw text with a background box on a frame.
    """
    h, w, _ = frame.shape
    
    # Settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    color_text = (255, 255, 255) # White
    color_bg = (0, 0, 0)         # Black
    
    # Get text size to create the background box
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    
    # Coordinates (Centered at bottom)
    x = (w - text_w) // 2
    y = h - 50
    
    # Draw background box (rectangle)
    cv2.rectangle(frame, (x - 10, y - text_h - 10), (x + text_w + 10, y + baseline + 10), color_bg, -1)
    
    # Draw text
    cv2.putText(frame, text, (x, y), font, font_scale, color_text, thickness, cv2.LINE_AA)
    return frame

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
        print(f"Translated to: English")
    segments = result["segments"]
    print("Transcription complete.")

    # 6. Handle audio-only files (output SRT and exit)
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

    # 7. Setup Video Capture (video files only from here)
    cap = cv2.VideoCapture(args.input_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # 6. Setup Video Writer (if output requested)
    out = None
    temp_video_path = None
    
    if args.output:
        # We write to a temp file first (OpenCV creates silent video)
        temp_video_path = f"temp_silent_{os.path.basename(args.output)}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
        print(f"Processing video frames to temporary file '{temp_video_path}'...")

    # 7. Process Frames
    start_time = time.time()
    
    print("Starting playback/processing...")
    if not args.no_show:
        print("Press 'q' to quit.")

    # Loop variables
    frame_idx = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate timestamp (in seconds) based on frame count and FPS
        current_timestamp = frame_idx / fps
        
        # Find active subtitle
        current_text = ""
        for seg in segments:
            if seg["start"] <= current_timestamp <= seg["end"]:
                current_text = seg["text"].strip()
                break

        # Draw the subtitle if text exists
        if current_text:
            frame = draw_subtitle(frame, current_text)

        # Write to file if output path was provided
        if out:
            out.write(frame)

        # Show live window if not disabled
        if not args.no_show:
            cv2.imshow('Whisper Subtitle Player', frame)
            
            # WaitKey controls playback speed. 
            delay = int(1000 / fps)
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break
        else:
            # Simple progress log if we aren't showing the video
            if frame_idx % 60 == 0:
                print(f"Processing: {int((frame_idx/total_frames)*100)}%", end='\r')

        frame_idx += 1

    # Cleanup OpenCV
    cap.release()
    if out:
        out.release()
    if not args.no_show:
        cv2.destroyAllWindows()
    print("\nVisual processing complete.")

    # 8. Merge Audio with FFmpeg
    if args.output and temp_video_path and os.path.exists(temp_video_path):
        if args.compress:
            print("Merging audio and compressing video (this will take longer)...")
        else:
            print("Merging original audio into final video...")
        
        try:
            if args.compress:
                # Compression mode: Re-encode video with H.264 and compress audio
                command = [
                    "ffmpeg",
                    "-y",                   # Overwrite output without asking
                    "-i", temp_video_path,  # Input 0: Silent video we just made
                    "-i", args.input_file, # Input 1: Original video with audio
                    "-c:v", "libx264",      # Use H.264 codec
                    "-crf", "28",           # Constant Rate Factor (18-28 is good, higher = smaller file)
                    "-preset", "medium",    # Encoding speed (slow = better compression)
                    "-c:a", "aac",          # AAC audio codec
                    "-b:a", "128k",         # Audio bitrate
                    "-map", "0:v:0",        # Map video from Input 0
                    "-map", "1:a:0",        # Map audio from Input 1
                    "-shortest",            # Stop when the shortest stream ends
                    args.output             # Final output file
                ]
            else:
                # Fast mode: Copy video stream without re-encoding
                command = [
                    "ffmpeg",
                    "-y",                   # Overwrite output without asking
                    "-i", temp_video_path,  # Input 0: Silent video we just made
                    "-i", args.input_file, # Input 1: Original video with audio
                    "-c:v", "copy",         # Copy video stream (don't re-encode)
                    "-c:a", "aac",          # Encode audio to AAC
                    "-map", "0:v:0",        # Map video from Input 0
                    "-map", "1:a:0",        # Map audio from Input 1
                    "-shortest",            # Stop when the shortest stream ends
                    args.output             # Final output file
                ]
            
            # Run the command silently
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Success! Final video with audio saved to: {args.output}")
            
            # Delete the temporary silent file
            os.remove(temp_video_path)
            
        except subprocess.CalledProcessError as e:
            print("Error merging audio with ffmpeg.")
            print(f"FFmpeg stderr: {e.stderr.decode()}")
            print(f"The silent video is still available at: {temp_video_path}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("Done.")

if __name__ == "__main__":
    main()