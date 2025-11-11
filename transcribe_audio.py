"""
Transcribe audio file using OpenAI Whisper API with retry logic
Supports both audio and video inputs (.mp3, .wav, .mp4, .mov, etc.)
"""

import os
import subprocess
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------------------------------------------------
# Helper: Convert video -> audio
# ---------------------------------------------------------------------
def convert_to_audio_if_needed(file_path):
    """
    Converts video to audio (.mp3) if needed.
    Returns the path to the audio file, or None if conversion fails.
    """
    ext = Path(file_path).suffix.lower()
    if ext in [".mp3", ".wav", ".m4a", ".webm", ".ogg"]:
        return file_path  # already audio

    print(f"🎬 Detected video file ({ext}). Converting to audio...")
    audio_path = str(Path(file_path).with_suffix(".mp3"))

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", file_path, "-q:a", "0", "-map", "a", audio_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        print(f"🎧 Converted video → {audio_path}")
        return audio_path
    except Exception as e:
        print(f"❌ Error converting video to audio: {e}")
        return None


# ---------------------------------------------------------------------
# Main Function: Transcribe Audio
# ---------------------------------------------------------------------
def transcribe_audio(audio_file_path, max_retries=3):
    """
    Transcribe audio using OpenAI Whisper API with retry logic
    
    Args:
        audio_file_path: Path to audio or video file
        max_retries: Maximum number of retry attempts
    
    Returns:
        dict: Transcript with text and segments
    """

    print(f"🎙️  Preparing file for transcription: {audio_file_path}")
    print("⏳ This may take a minute...")

    # Convert video → audio if needed
    audio_file_path = convert_to_audio_if_needed(audio_file_path)
    if not audio_file_path or not os.path.exists(audio_file_path):
        print("❌ Failed to prepare audio file.")
        return None

    # Check file size (Whisper has 25MB limit)
    file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
    if file_size_mb > 25:
        print(f"⚠️  Warning: File is {file_size_mb:.1f}MB. Whisper API limit is 25MB.")
        print("   Consider compressing or trimming the file first.")
        return None

    for attempt in range(max_retries):
        try:
            with open(audio_file_path, "rb") as audio_file:
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )

            print("✅ Transcription complete!")

            # Handle response
            if hasattr(transcript, 'text'):
                transcript_text = transcript.text
                duration = getattr(transcript, 'duration', 0)
            elif isinstance(transcript, dict):
                transcript_text = transcript.get('text', '')
                duration = transcript.get('duration', 0)
            else:
                transcript_text = str(transcript)
                duration = 0

            if not transcript_text:
                print("⚠️  Warning: Empty transcript received")
                if attempt < max_retries - 1:
                    print(f"   Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                return None

            # Prepare result
            result = {
                "text": transcript_text,
                "language": "en",
                "duration": duration,
                "segments": []
            }

            if hasattr(transcript, 'segments'):
                for seg in transcript.segments:
                    if isinstance(seg, dict):
                        result["segments"].append({
                            "start": seg.get('start', 0),
                            "end": seg.get('end', 0),
                            "text": seg.get('text', '')
                        })
                    elif hasattr(seg, 'start'):
                        result["segments"].append({
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text
                        })

            if not result["segments"]:
                result["segments"].append({
                    "start": 0,
                    "end": duration,
                    "text": transcript_text
                })

            # Save transcript to JSON
            output_file = str(Path(audio_file_path).with_suffix("_transcript.json"))
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2)

            print(f"💾 Saved transcript to: {output_file}")
            print(f"\n📊 Summary:")
            if duration > 0:
                print(f"   Duration: {duration:.1f} seconds")
            print(f"   Word count: ~{len(result['text'].split())} words")
            print(f"\n📝 First 200 characters:\n   {result['text'][:200]}...")

            # Cleanup temp audio if it was converted
            if Path(audio_file_path).suffix == ".mp3" and not audio_file_path.endswith(".original.mp3"):
                original_ext = Path(audio_file_path).stem
                if not original_ext.endswith("mp3"):  # i.e., came from mp4
                    os.remove(audio_file_path)
                    print(f"🧹 Deleted temporary audio: {audio_file_path}")

            return result

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error during transcription (attempt {attempt + 1}/{max_retries}): {error_msg}")

            if "500" in error_msg or "503" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"   OpenAI server error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            elif "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    print(f"   Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            elif "413" in error_msg or "file too large" in error_msg.lower():
                print("   File is too large for Whisper API (max 25MB).")
                return None

            if attempt == max_retries - 1:
                print("\n💥 All retry attempts failed!")
                import traceback
                traceback.print_exc()
                return None


# ---------------------------------------------------------------------
# Local Test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    audio_file = "test_meeting.mp4"

    if not os.path.exists(audio_file):
        print(f"❌ Error: {audio_file} not found!")
        print("Available files:")
        for f in os.listdir('.'):
            if f.endswith(('.mp3', '.mp4', '.wav', '.webm', '.m4a', '.avi', '.mov')):
                print(f"   - {f}")
    else:
        result = transcribe_audio(audio_file)
        if result:
            print("\n✅ Transcription successful!")
            print("Next step: Run generate_mom.py to create Minutes of Meeting")
        else:
            print("\n❌ Transcription failed after all retries")
