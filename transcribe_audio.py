"""
Transcribe audio file using OpenAI Whisper API with retry logic
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import time

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file_path, max_retries=3):
    """
    Transcribe audio using OpenAI Whisper API with retry logic
    
    Args:
        audio_file_path: Path to audio file (mp3, mp4, wav, webm, etc.)
        max_retries: Maximum number of retry attempts
    
    Returns:
        dict: Transcript with text and segments
    """
    
    print(f"🎙️  Transcribing: {audio_file_path}")
    print("⏳ This may take a minute...")
    
    # Check file size (Whisper has 25MB limit)
    file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)
    if file_size_mb > 25:
        print(f"⚠️  Warning: File is {file_size_mb:.1f}MB. Whisper API limit is 25MB.")
        print("   Consider compressing the file first.")
        return None
    
    for attempt in range(max_retries):
        try:
            # Open audio file
            with open(audio_file_path, "rb") as audio_file:
                # Call Whisper API
                print(f"   Attempt {attempt + 1}/{max_retries}...")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )
            
            print("✅ Transcription complete!")
            
            # Handle response - it might be a dict or an object
            if hasattr(transcript, 'text'):
                # It's an object
                transcript_text = transcript.text
                duration = getattr(transcript, 'duration', 0)
            elif isinstance(transcript, dict):
                # It's a dict
                transcript_text = transcript.get('text', '')
                duration = transcript.get('duration', 0)
            else:
                # Fallback
                transcript_text = str(transcript)
                duration = 0
            
            if not transcript_text:
                print("⚠️  Warning: Empty transcript received")
                if attempt < max_retries - 1:
                    print(f"   Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                return None
            
            # Extract data
            result = {
                "text": transcript_text,
                "language": "en",
                "duration": duration,
                "segments": []
            }
            
            # Try to add segments if available
            if hasattr(transcript, 'segments'):
                for segment in transcript.segments:
                    if isinstance(segment, dict):
                        result["segments"].append({
                            "start": segment.get('start', 0),
                            "end": segment.get('end', 0),
                            "text": segment.get('text', '')
                        })
                    elif hasattr(segment, 'start'):
                        result["segments"].append({
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text
                        })
            
            # If no segments, create one for the whole text
            if not result["segments"]:
                result["segments"].append({
                    "start": 0,
                    "end": duration,
                    "text": transcript_text
                })
            
            # Save to file
            output_file = audio_file_path.replace('.mp3', '_transcript.json')\
                .replace('.webm', '_transcript.json')\
                .replace('.wav', '_transcript.json')\
                .replace('.m4a', '_transcript.json')\
                .replace('.mp4', '_transcript.json')\
                .replace('.avi', '_transcript.json')\
                .replace('.mov', '_transcript.json')
            
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"💾 Saved transcript to: {output_file}")
            
            # Print summary
            print(f"\n📊 Summary:")
            if duration > 0:
                print(f"   Duration: {duration:.1f} seconds")
            print(f"   Word count: ~{len(result['text'].split())} words")
            print(f"\n📝 First 200 characters:")
            print(f"   {result['text'][:200]}...")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error during transcription (attempt {attempt + 1}/{max_retries}): {error_msg}")
            
            # Check if it's a rate limit or server error
            if "500" in error_msg or "503" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"   OpenAI server error. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            elif "429" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                    print(f"   Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            elif "413" in error_msg or "file too large" in error_msg.lower():
                print("   File is too large for Whisper API (max 25MB).")
                return None
            
            # If last attempt, show full traceback
            if attempt == max_retries - 1:
                print("\n💥 All retry attempts failed!")
                import traceback
                traceback.print_exc()
                return None

if __name__ == "__main__":
    # Test with sample audio file
    audio_file = "test_meeting.mp3"
    
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