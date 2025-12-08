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
    parser = argparse.ArgumentParser(description="Generate subtitles for a video using OpenAI Whisper.")
    
    # Input video file (Required)
    parser.add_argument("input_video", type=str, help="Path to the input video file.")
    
    # Output video file (Optional)
    parser.add_argument("-o", "--output", type=str, help="Path to save the output video.")
    
    # Flag to hide the live window (Optional)
    parser.add_argument("--no-show", action="store_true", help="Do not show the video window live (faster processing).")
    
    # Model selection (Optional)
    parser.add_argument("--model", type=str, default="base", choices=["tiny", "base", "small", "medium", "large"], help="Whisper model size.")
    
    # Compression flag (Optional)
    parser.add_argument("--compress", action="store_true", help="Compress output video significantly (reduces file size, slower processing).")

    # Language (Optional)
    parser.add_argument("--language", type=str, default=None, help="Language code for transcription (e.g., 'en', 'az', 'ru'). Auto-detects if not specified.")

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
    if not os.path.exists(args.input_video):
        print(f"Error: Input file '{args.input_video}' not found.")
        sys.exit(1)

    # 2. Auto-detect Headless Environment
    if is_headless():
        if not args.no_show:
            print("\nWARNING: No display detected (Headless environment).")
            print("         Disabling live window to prevent crashes.")
            args.no_show = True
        
        if not args.output:
            print("         WARNING: You are in headless mode but didn't specify an output file.")
            print("         The script will run but you won't see the result.")
            print("         Use -o output.mp4 to save the result.\n")

    # 3. Load Whisper Model
    print(f"Loading Whisper model ('{args.model}')...")
    model = whisper.load_model(args.model)

    # 4. Transcribe
    print("Transcribing audio... (This may take some time depending on video length)")
    # We use fp16=False to avoid warnings if you are on a CPU
    transcribe_options = {"fp16": False}
    if args.language:
        transcribe_options["language"] = args.language
        print(f"Using specified language: {args.language}")
    result = model.transcribe(args.input_video, **transcribe_options)
    print(f"Detected/used language: {result['language']}")
    segments = result["segments"]
    print("Transcription complete.")

    # 5. Setup Video Capture
    cap = cv2.VideoCapture(args.input_video)
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
                    "-i", args.input_video, # Input 1: Original video with audio
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
                    "-i", args.input_video, # Input 1: Original video with audio
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