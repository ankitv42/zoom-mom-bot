"""
Complete workflow: Audio → Transcript → MOM → Email
"""

import os
import sys
from transcribe_audio import transcribe_audio
from generate_mom import generate_mom
from email_service import send_mom_email

def process_meeting_complete(audio_file, recipient_emails, meeting_title=None):
    """
    Complete workflow to process a meeting recording
    
    Args:
        audio_file: Path to audio file
        recipient_emails: Email(s) to send MOM to (string or list)
        meeting_title: Optional meeting title
    
    Returns:
        dict: Status of each step
    """
    
    print("="*60)
    print("🚀 STARTING COMPLETE MEETING PROCESSING")
    print("="*60)
    
    result = {
        "transcription": None,
        "mom_generation": None,
        "email": None
    }
    
    # Step 1: Transcribe
    print("\n📍 STEP 1/3: Transcribing audio...")
    transcript_result = transcribe_audio(audio_file)
    
    if not transcript_result:
        print("❌ Transcription failed. Aborting.")
        return result
    
    result["transcription"] = "success"
    transcript_file = audio_file.replace('.mp3', '_transcript.json').replace('.webm', '_transcript.json')
    
    # Step 2: Generate MOM
    print("\n📍 STEP 2/3: Generating MOM...")
    mom_data = generate_mom(transcript_file)
    
    if not mom_data:
        print("❌ MOM generation failed. Aborting.")
        return result
    
    result["mom_generation"] = "success"
    
    # Step 3: Send Email
    print("\n📍 STEP 3/3: Sending email...")
    
    if not meeting_title:
        meeting_title = "Team Meeting"
    
    email_result = send_mom_email(
        to_emails=recipient_emails,
        mom_data=mom_data,
        meeting_title=meeting_title
    )
    
    if email_result["status"] == "success":
        result["email"] = "success"
        print("\n" + "="*60)
        print("✅ COMPLETE WORKFLOW SUCCESSFUL!")
        print("="*60)
        print(f"✅ Transcription: Done")
        print(f"✅ MOM Generation: Done")
        print(f"✅ Email Sent: Done")
        print(f"\n📧 Email sent to: {', '.join(email_result['recipients'])}")
    else:
        result["email"] = "failed"
        print(f"\n❌ Email sending failed: {email_result['message']}")
    
    return result

if __name__ == "__main__":
    print("🎬 Complete Meeting Processor")
    print("="*60)
    
    # Get audio file
    audio_file = input("Enter audio file path (or press Enter for test_meeting.mp3): ").strip()
    if not audio_file:
        audio_file = "test_meeting.mp3"
    
    if not os.path.exists(audio_file):
        print(f"❌ Error: {audio_file} not found!")
        sys.exit(1)
    
    # Get recipient email
    recipient = input("Enter recipient email (or multiple, comma-separated): ").strip()
    if not recipient:
        print("❌ Error: Email is required!")
        sys.exit(1)
    
    # Convert to list if multiple
    recipients = [email.strip() for email in recipient.split(',')]
    
    # Get meeting title
    meeting_title = input("Enter meeting title (or press Enter for 'Team Meeting'): ").strip()
    if not meeting_title:
        meeting_title = "Team Meeting"
    
    # Process
    result = process_meeting_complete(audio_file, recipients, meeting_title)
    
    print("\n" + "="*60)
    print("📊 FINAL STATUS")
    print("="*60)
    for step, status in result.items():
        emoji = "✅" if status == "success" else "❌" if status == "failed" else "⏭️"
        print(f"{emoji} {step.replace('_', ' ').title()}: {status or 'skipped'}")
