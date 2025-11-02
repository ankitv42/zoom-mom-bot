"""
Generate Minutes of Meeting (MOM) from transcript using GPT-4
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_mom(transcript_file):
    """
    Generate structured MOM from transcript
    
    Args:
        transcript_file: Path to transcript JSON file
    
    Returns:
        dict: Structured MOM with summary, decisions, action items, etc.
    """
    
    print(f"📄 Reading transcript: {transcript_file}")
    
    # Load transcript
    with open(transcript_file, 'r') as f:
        transcript_data = json.load(f)
    
    transcript_text = transcript_data.get('text', '')
    
    if not transcript_text:
        print("❌ Error: Transcript is empty!")
        return None
    
    print(f"📝 Transcript length: {len(transcript_text)} characters")
    print("🤖 Generating MOM with GPT-4...")
    print("⏳ This may take 10-30 seconds...")
    
    # Create prompt for GPT-4
    prompt = f"""You are an expert meeting assistant. Analyze the following meeting transcript and generate a structured Minutes of Meeting (MOM).

TRANSCRIPT:
{transcript_text}

Please extract and format the following information in JSON format:

1. **summary**: A brief 2-3 sentence overview of what was discussed
2. **key_points**: Array of main discussion points (3-5 bullet points)
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
7. **attendees**: List of people mentioned in the meeting (if identifiable from transcript)

Return ONLY valid JSON, no additional text.
"""

    try:
        # Call GPT-4
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for POC (gpt-4o-mini)
            messages=[
                {"role": "system", "content": "You are a professional meeting assistant that creates clear, structured minutes of meetings. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            response_format={"type": "json_object"}  # Force JSON output
        )
        
        # Parse response
        mom_json = response.choices[0].message.content
        mom = json.loads(mom_json)
        
        print("✅ MOM generated successfully!")
        
        # Add metadata
        mom['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'transcript_file': transcript_file,
            'model_used': 'gpt-4o-mini',
            'transcript_length': len(transcript_text),
            'duration': transcript_data.get('duration', 'Unknown')
        }
        
        # Save to file
        output_file = transcript_file.replace('_transcript.json', '_mom.json')
        with open(output_file, 'w') as f:
            json.dump(mom, f, indent=2)
        
        print(f"💾 Saved MOM to: {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📋 MINUTES OF MEETING - SUMMARY")
        print("="*60)
        print(f"\n📝 Summary:\n{mom.get('summary', 'N/A')}")
        
        if mom.get('decisions'):
            print(f"\n✅ Decisions Made ({len(mom['decisions'])}):")
            for i, decision in enumerate(mom['decisions'], 1):
                print(f"   {i}. {decision.get('decision', 'N/A')}")
                if decision.get('made_by'):
                    print(f"      → Decided by: {decision['made_by']}")
        
        if mom.get('action_items'):
            print(f"\n📌 Action Items ({len(mom['action_items'])}):")
            for i, item in enumerate(mom['action_items'], 1):
                print(f"   {i}. {item.get('task', 'N/A')}")
                print(f"      → Owner: {item.get('owner', 'Unassigned')}")
                print(f"      → Deadline: {item.get('deadline', 'Not specified')}")
                print(f"      → Priority: {item.get('priority', 'medium')}")
        
        if mom.get('questions'):
            print(f"\n❓ Open Questions ({len(mom['questions'])}):")
            for i, question in enumerate(mom['questions'], 1):
                print(f"   {i}. {question}")
        
        print("\n" + "="*60)
        
        return mom
        
    except Exception as e:
        print(f"❌ Error generating MOM: {e}")
        return None

if __name__ == "__main__":
    # Find transcript file
    #transcript_file = "test_meeting_transcript.json"
    transcript_file = "sample_9min_transcript.json"
    
    if not os.path.exists(transcript_file):
        print(f"❌ Error: {transcript_file} not found!")
        print("Please run transcribe_audio.py first")
    else:
        mom = generate_mom(transcript_file)
        
        if mom:
            print("\n✅ MOM generation complete!")
            print("\nNext steps:")
            print("  1. Review the MOM in test_meeting_mom.json")
            print("  2. Tomorrow we'll build the email sender")
