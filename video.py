import os
import time
import subprocess

import cv2


def draw_subtitle(frame, text):
    """
    Helper function to draw text with a background box on a frame.
    """
    h, w, _ = frame.shape

    # Settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    color_text = (255, 255, 255)  # White
    color_bg = (0, 0, 0)          # Black

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


def process_video(input_file, output_path, segments, no_show=False, compress=False):
    """
    Process video frames, overlay subtitles, and optionally save output.

    Args:
        input_file: Path to input video file
        output_path: Path to save output video (None to skip saving)
        segments: Transcription segments from Whisper
        no_show: If True, don't show live preview window
        compress: If True, compress the output video
    """
    # Setup Video Capture
    cap = cv2.VideoCapture(input_file)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Setup Video Writer (if output requested)
    out = None
    temp_video_path = None

    if output_path:
        # We write to a temp file first (OpenCV creates silent video)
        temp_video_path = f"temp_silent_{os.path.basename(output_path)}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
        print(f"Processing video frames to temporary file '{temp_video_path}'...")

    # Process Frames
    start_time = time.time()

    print("Starting playback/processing...")
    if not no_show:
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
        if not no_show:
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
    if not no_show:
        cv2.destroyAllWindows()
    print("\nVisual processing complete.")

    # Merge Audio with FFmpeg
    if output_path and temp_video_path and os.path.exists(temp_video_path):
        _merge_audio(input_file, output_path, temp_video_path, compress)


def _merge_audio(input_file, output_path, temp_video_path, compress):
    """
    Merge audio from original file into the processed video using FFmpeg.
    """
    if compress:
        print("Merging audio and compressing video (this will take longer)...")
    else:
        print("Merging original audio into final video...")

    try:
        if compress:
            # Compression mode: Re-encode video with H.264 and compress audio
            command = [
                "ffmpeg",
                "-y",                   # Overwrite output without asking
                "-i", temp_video_path,  # Input 0: Silent video we just made
                "-i", input_file,       # Input 1: Original video with audio
                "-c:v", "libx264",      # Use H.264 codec
                "-crf", "28",           # Constant Rate Factor (18-28 is good, higher = smaller file)
                "-preset", "medium",    # Encoding speed (slow = better compression)
                "-c:a", "aac",          # AAC audio codec
                "-b:a", "128k",         # Audio bitrate
                "-map", "0:v:0",        # Map video from Input 0
                "-map", "1:a:0",        # Map audio from Input 1
                "-shortest",            # Stop when the shortest stream ends
                output_path             # Final output file
            ]
        else:
            # Fast mode: Copy video stream without re-encoding
            command = [
                "ffmpeg",
                "-y",                   # Overwrite output without asking
                "-i", temp_video_path,  # Input 0: Silent video we just made
                "-i", input_file,       # Input 1: Original video with audio
                "-c:v", "copy",         # Copy video stream (don't re-encode)
                "-c:a", "aac",          # Encode audio to AAC
                "-map", "0:v:0",        # Map video from Input 0
                "-map", "1:a:0",        # Map audio from Input 1
                "-shortest",            # Stop when the shortest stream ends
                output_path             # Final output file
            ]

        # Run the command silently
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Success! Final video with audio saved to: {output_path}")

        # Delete the temporary silent file
        os.remove(temp_video_path)

    except subprocess.CalledProcessError as e:
        print("Error merging audio with ffmpeg.")
        print(f"FFmpeg stderr: {e.stderr.decode()}")
        print(f"The silent video is still available at: {temp_video_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
