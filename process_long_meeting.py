"""
Enhanced processor for long meetings with better error handling
"""

import os
import sys
import json
from openai import OpenAI
from dotenv import load_dotenv
from transcribe_audio import transcribe_audio
from email_service import send_mom_email

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chunk_transcript(transcript_text, max_words=3000):
    """
    Split long transcript into chunks for processing
    
    Args:
        transcript_text: Full transcript text
        max_words: Maximum words per chunk
    
    Returns:
        list: List of transcript chunks
    """
    words = transcript_text.split()
    chunks = []
    
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    
    return chunks

def generate_mom_for_long_meeting(transcript_file):
    """
    Generate MOM for long meetings by processing in chunks if needed
    """
    
    print(f"📄 Reading transcript: {transcript_file}")
    
    with open(transcript_file, 'r') as f:
        transcript_data = json.load(f)
    
    transcript_text = transcript_data.get('text', '')
    duration = transcript_data.get('duration', 0)
    
    if not transcript_text:
        print("❌ Error: Transcript is empty!")
        return None
    
    word_count = len(transcript_text.split())
    print(f"📝 Transcript stats:")
    print(f"   Duration: {duration/60:.1f} minutes")
    print(f"   Characters: {len(transcript_text):,}")
    print(f"   Words: {word_count:,}")
    
    # Check if transcript is too long (>4000 words = potential token limit issue)
    if word_count > 4000:
        print(f"⚠️  Long transcript detected ({word_count} words)")
        print("   Using chunked processing strategy...")
        return generate_mom_chunked(transcript_text, transcript_data)
    else:
        print("   Normal processing (transcript size is manageable)")
        return generate_mom_normal(transcript_text, transcript_data)

def generate_mom_normal(transcript_text, transcript_data):
    """Generate MOM for normal-length transcripts"""
    
    print("🤖 Generating MOM with GPT-4...")
    print("⏳ This may take 30-60 seconds...")
    
    from datetime import datetime
    
    prompt = f"""You are an expert meeting assistant. Analyze the following meeting transcript and generate a structured Minutes of Meeting (MOM).

TRANSCRIPT:
{transcript_text}

Please extract and format the following information in JSON format:

1. **summary**: A comprehensive 3-5 sentence overview of what was discussed
2. **key_points**: Array of main discussion points (5-8 bullet points)
3. **decisions**: Array of decisions made, each with:
   - decision: The decision text
   - made_by: Who made the decision (if mentioned, otherwise "Team")
   - timestamp: Approximate time in transcript (if possible)
4. **action_items**: Array of tasks, each with:
   - task: What needs to be done
   - owner: Who is responsible (if mentioned, otherwise "Unassigned")
   - deadline: Deadline if mentioned (otherwise "Not specified")
   - priority: high/medium/low based on context
5. **questions**: Array of unresolved questions or concerns raised
6. **next_steps**: What should happen after this meeting
7. **attendees**: List of people mentioned in the meeting (if identifiable)
8. **topics_discussed**: Main topics/agenda items covered

Return ONLY valid JSON, no additional text.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional meeting assistant that creates clear, structured minutes of meetings. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        mom_json = response.choices[0].message.content
        mom = json.loads(mom_json)
        
        # Add metadata
        mom['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'duration': transcript_data.get('duration', 0),
            'word_count': len(transcript_text.split()),
            'processing_method': 'normal'
        }
        
        print("✅ MOM generated successfully!")
        return mom
        
    except Exception as e:
        print(f"❌ Error generating MOM: {e}")
        return None

def generate_mom_chunked(transcript_text, transcript_data):
    """Generate MOM for very long transcripts using chunked processing"""
    
    from datetime import datetime
    
    print("🔀 Processing in chunks...")
    
    # Split into chunks
    chunks = chunk_transcript(transcript_text, max_words=3000)
    print(f"   Split into {len(chunks)} chunks")
    
    chunk_summaries = []
    all_decisions = []
    all_action_items = []
    all_questions = []
    
    # Process each chunk
    for i, chunk in enumerate(chunks, 1):
        print(f"\n   Processing chunk {i}/{len(chunks)}...")
        
        prompt = f"""Analyze this portion of a meeting transcript and extract key information.

TRANSCRIPT SEGMENT:
{chunk}

Extract:
1. Key points discussed in this segment
2. Any decisions made
3. Any action items assigned
4. Any questions raised

Return as JSON with keys: key_points, decisions, action_items, questions
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Extract key information from meeting segments. Return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            chunk_result = json.loads(response.choices[0].message.content)
            
            # Collect results
            if chunk_result.get('key_points'):
                chunk_summaries.extend(chunk_result['key_points'])
            if chunk_result.get('decisions'):
                all_decisions.extend(chunk_result['decisions'])
            if chunk_result.get('action_items'):
                all_action_items.extend(chunk_result['action_items'])
            if chunk_result.get('questions'):
                all_questions.extend(chunk_result['questions'])
            
            print(f"   ✅ Chunk {i} processed")
            
        except Exception as e:
            print(f"   ⚠️  Error in chunk {i}: {e}")
            continue
    
    # Now create final comprehensive summary
    print("\n🔄 Creating final comprehensive MOM...")
    
    combined_info = f"""
Key Points: {json.dumps(chunk_summaries[:20])}  
Decisions: {json.dumps(all_decisions)}
Action Items: {json.dumps(all_action_items)}
Questions: {json.dumps(all_questions)}
"""
    
    final_prompt = f"""Based on the extracted information from a long meeting, create a comprehensive MOM.

EXTRACTED INFORMATION:
{combined_info}

Create a final MOM with:
1. summary: 3-5 sentence overall summary
2. key_points: Top 8-10 most important points
3. decisions: All decisions (remove duplicates)
4. action_items: All action items (remove duplicates)
5. questions: All unresolved questions
6. next_steps: Recommended next steps
7. topics_discussed: Main topics covered

Return valid JSON only.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Create comprehensive meeting minutes. Return valid JSON."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        mom = json.loads(response.choices[0].message.content)
        
        # Add metadata
        mom['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'duration': transcript_data.get('duration', 0),
            'word_count': len(transcript_text.split()),
            'chunks_processed': len(chunks),
            'processing_method': 'chunked'
        }
        
        print("✅ Comprehensive MOM generated!")
        return mom
        
    except Exception as e:
        print(f"❌ Error creating final MOM: {e}")
        return None

if __name__ == "__main__":
    print("🎬 Long Meeting Processor")
    print("="*60)
    
    # Get audio file
    audio_file = input("Enter audio file path (default: long_meeting.mp3): ").strip()
    if not audio_file:
        audio_file = "long_meeting.mp3"
    
    if not os.path.exists(audio_file):
        print(f"❌ Error: {audio_file} not found!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🚀 STARTING PROCESSING")
    print("="*60)
    
    # Step 1: Transcribe
    print("\n📍 STEP 1/3: Transcribing audio...")
    print("⏳ For a long meeting, this will take several minutes...")
    
    transcript_result = transcribe_audio(audio_file)
    
    if not transcript_result:
        print("❌ Transcription failed.")
        sys.exit(1)
    
    transcript_file = audio_file.replace('.mp3', '_transcript.json').replace('.webm', '_transcript.json')
    
    # Step 2: Generate MOM
    print("\n📍 STEP 2/3: Generating MOM...")
    mom_data = generate_mom_for_long_meeting(transcript_file)
    
    if not mom_data:
        print("❌ MOM generation failed.")
        sys.exit(1)
    
    # Save MOM
    mom_file = audio_file.replace('.mp3', '_mom.json').replace('.webm', '_mom.json')
    with open(mom_file, 'w') as f:
        json.dump(mom_data, f, indent=2)
    
    print(f"💾 Saved MOM to: {mom_file}")
    
    # Print summary
    print("\n" + "="*60)
    print("📋 MOM SUMMARY")
    print("="*60)
    print(f"\n📝 Summary:\n{mom_data.get('summary', 'N/A')}")
    
    if mom_data.get('key_points'):
        print(f"\n🔑 Key Points ({len(mom_data['key_points'])}):")
        for i, point in enumerate(mom_data['key_points'][:5], 1):
            print(f"   {i}. {point}")
        if len(mom_data['key_points']) > 5:
            print(f"   ... and {len(mom_data['key_points']) - 5} more")
    
    if mom_data.get('decisions'):
        print(f"\n✅ Decisions ({len(mom_data['decisions'])}):")
        for i, decision in enumerate(mom_data['decisions'][:3], 1):
            print(f"   {i}. {decision.get('decision', 'N/A')}")
        if len(mom_data['decisions']) > 3:
            print(f"   ... and {len(mom_data['decisions']) - 3} more")
    
    if mom_data.get('action_items'):
        print(f"\n📌 Action Items ({len(mom_data['action_items'])}):")
        for i, item in enumerate(mom_data['action_items'][:3], 1):
            print(f"   {i}. {item.get('task', 'N/A')}")
            print(f"      → Owner: {item.get('owner', 'Unassigned')}")
        if len(mom_data['action_items']) > 3:
            print(f"   ... and {len(mom_data['action_items']) - 3} more")
    
    # Step 3: Ask about email
    print("\n" + "="*60)
    print("📍 STEP 3/3: Email")
    print("="*60)
    
    send_email = input("\nSend MOM via email? (y/n): ").strip().lower()
    
    if send_email == 'y':
        recipient = input("Enter recipient email: ").strip()
        meeting_title = input("Enter meeting title: ").strip() or "Long Team Meeting"
        
        if recipient:
            result = send_mom_email(recipient, mom_data, meeting_title)
            
            if result['status'] == 'success':
                print("\n✅ Email sent successfully!")
            else:
                print(f"\n❌ Email failed: {result['message']}")
    
    print("\n" + "="*60)
    print("✅ PROCESSING COMPLETE!")
    print("="*60)
    print(f"📁 Files created:")
    print(f"   - {transcript_file}")
    print(f"   - {mom_file}")
