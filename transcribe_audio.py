"""
Transcribe audio file using OpenAI Whisper API
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file_path):
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_file_path: Path to audio file (mp3, mp4, wav, webm, etc.)
    
    Returns:
        dict: Transcript with text and segments
    """
    
    print(f"🎙️  Transcribing: {audio_file_path}")
    print("⏳ This may take a minute...")
    
    try:
        # Open audio file
        with open(audio_file_path, "rb") as audio_file:
            # Call Whisper API - use simple format first
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="json"  # Changed from verbose_json to json
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
        output_file = audio_file_path.replace('.mp3', '_transcript.json').replace('.webm', '_transcript.json').replace('.wav', '_transcript.json').replace('.m4a', '_transcript.json')
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
        print(f"❌ Error during transcription: {e}")
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
            if f.endswith(('.mp3', '.mp4', '.wav', '.webm')):
                print(f"   - {f}")
    else:
        result = transcribe_audio(audio_file)
        
        if result:
            print("\n✅ Transcription successful!")
            print("Next step: Run generate_mom.py to create Minutes of Meeting")