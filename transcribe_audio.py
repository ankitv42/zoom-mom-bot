"""
Transcribe audio file using OpenAI Whisper API
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Initialize OpenAI client
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
            # Call Whisper API
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",  # Get timestamps
                language="en"  # Optional: specify language
            )
        
        print("✅ Transcription complete!")
        
        # Extract main data
        result = {
            "text": transcript.text,
            "language": getattr(transcript, "language", "unknown"),
            "duration": getattr(transcript, "duration", 0),
            "segments": []
        }
        
        # Add segments with timestamps
        if hasattr(transcript, 'segments') and transcript.segments:
            for segment in transcript.segments:
                result["segments"].append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
        
        # Save to JSON file
        output_file = (
            audio_file_path.replace('.mp3', '_transcript.json')
                          .replace('.webm', '_transcript.json')
                          .replace('.wav', '_transcript.json')
                          .replace('.mp4', '_transcript.json')
        )
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved transcript to: {output_file}")
        
        # Print quick summary
        print(f"\n📊 Summary:")
        print(f"   Duration: {result['duration']:.1f} seconds")
        print(f"   Language: {result['language']}")
        print(f"   Word count: ~{len(result['text'].split())} words")
        print(f"\n📝 First 200 characters:")
        print(f"   {result['text'][:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None


if __name__ == "__main__":
    # Transcribe the audio file
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
