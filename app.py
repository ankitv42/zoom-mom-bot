"""
MOM Bot - Streamlit Web Interface
Main application file
"""

import streamlit as st
import os
import json
from datetime import datetime
import time
from pathlib import Path

from dotenv import load_dotenv  # 👈 ADD THIS
load_dotenv()  # 👈 ENSURE .env IS LOADED HERE

# Import our existing modules
from transcribe_audio import transcribe_audio
from generate_mom import generate_mom
from email_service import send_mom_email

# Page configuration
st.set_page_config(
    page_title="MOM Bot - AI Meeting Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 4px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_meetings' not in st.session_state:
    st.session_state.processed_meetings = []

if 'current_mom' not in st.session_state:
    st.session_state.current_mom = None

if 'current_transcript' not in st.session_state:
    st.session_state.current_transcript = None

# Create directories
Path("uploads").mkdir(exist_ok=True)
Path("transcripts").mkdir(exist_ok=True)
Path("moms").mkdir(exist_ok=True)

def format_duration(seconds):
    """Format duration in seconds to readable format"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"

def save_uploaded_file(uploaded_file):
    """Save uploaded file to disk"""
    file_path = os.path.join("uploads", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def process_audio_file(file_path, meeting_title):
    """Process audio file through complete pipeline"""
    
    results = {
        'success': False,
        'transcript': None,
        'mom': None,
        'transcript_file': None,
        'mom_file': None,
        'error': None
    }
    
    try:
        # Step 1: Transcription
        st.info("🎙️ Step 1/3: Transcribing audio...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Sending audio to Whisper API...")
        try:
            transcript_result = transcribe_audio(file_path)
            
            if not transcript_result:
                results['error'] = "Transcription failed after 3 attempts. OpenAI API might be temporarily down. Please try again in a few minutes."
                return results
        except Exception as e:
            results['error'] = f"Transcription error: {str(e)}"
            return results
        
        progress_bar.progress(33)
        status_text.text("✅ Transcription complete!")
        
        
        # Save transcript
        transcript_file = file_path.replace('uploads/', 'transcripts/').replace('.mp3', '_transcript.json').replace('.webm', '_transcript.json').replace('.wav', '_transcript.json').replace('.m4a', '_transcript.json')
        
        
        with open(transcript_file, "w") as f:
            json.dump(transcript_result, f, indent=2)  # ✅ write the actual transcription
        
        results['transcript'] = transcript_result
        results['transcript_file'] = transcript_file
        
        # Step 2: MOM Generation
        st.info("🤖 Step 2/3: Generating Minutes of Meeting...")
        status_text.text("Analyzing transcript with GPT-4...")
        
        mom_data = generate_mom(transcript_file)
        
        if not mom_data:
            results['error'] = "MOM generation failed"
            return results
        
        progress_bar.progress(66)
        status_text.text("✅ MOM generated successfully!")
        
        # Save MOM
        mom_file = transcript_file.replace('transcripts/', 'moms/').replace('_transcript.json', '_mom.json')
        with open(mom_file, 'w') as f:
            json.dump(mom_data, f, indent=2)
        
        results['mom'] = mom_data
        results['mom_file'] = mom_file
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        results['success'] = True
        
        # Save to session state
        st.session_state.processed_meetings.append({
            'title': meeting_title,
            'date': datetime.now().isoformat(),
            'transcript_file': transcript_file,
            'mom_file': mom_file,
            'duration': transcript_result.get('duration', 0)
        })
        
        st.session_state.current_mom = mom_data
        st.session_state.current_transcript = transcript_result
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

def display_mom(mom_data):
    """Display MOM in a formatted way"""
    
    st.markdown("---")
    st.markdown("## 📋 Minutes of Meeting")
    
    # Summary
    if mom_data.get('summary'):
        st.markdown("### 📝 Summary")
        st.info(mom_data['summary'])
    
    # Key Points
    if mom_data.get('key_points'):
        st.markdown("### 🔑 Key Discussion Points")
        for i, point in enumerate(mom_data['key_points'], 1):
            st.markdown(f"{i}. {point}")
    
    # Decisions
    if mom_data.get('decisions'):
        st.markdown("### ✅ Decisions Made")
        for i, decision in enumerate(mom_data['decisions'], 1):
            with st.expander(f"Decision {i}: {decision.get('decision', 'N/A')[:50]}..."):
                st.write(f"**Decision:** {decision.get('decision', 'N/A')}")
                st.write(f"**Decided by:** {decision.get('made_by', 'Team')}")
                if decision.get('timestamp'):
                    st.write(f"**Time:** {decision.get('timestamp')}")
    
    # Action Items
    if mom_data.get('action_items'):
        st.markdown("### 📌 Action Items")
        for i, item in enumerate(mom_data['action_items'], 1):
            priority = item.get('priority', 'medium')
            priority_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(priority, '⚪')
            
            with st.expander(f"{priority_color} Action {i}: {item.get('task', 'N/A')[:50]}..."):
                st.write(f"**Task:** {item.get('task', 'N/A')}")
                st.write(f"**Owner:** {item.get('owner', 'Unassigned')}")
                st.write(f"**Deadline:** {item.get('deadline', 'Not specified')}")
                st.write(f"**Priority:** {priority.upper()}")
    
    # Questions
    if mom_data.get('questions'):
        st.markdown("### ❓ Open Questions")
        for i, question in enumerate(mom_data['questions'], 1):
            st.markdown(f"{i}. {question}")
    
    # Next Steps
    if mom_data.get('next_steps'):
        st.markdown("### 🚀 Next Steps")
        st.info(mom_data['next_steps'])
    
    # Attendees
    if mom_data.get('attendees'):
        st.markdown("### 👥 Attendees")
        cols = st.columns(len(mom_data['attendees']) if len(mom_data['attendees']) < 5 else 5)
        for i, attendee in enumerate(mom_data['attendees']):
            cols[i % 5].markdown(f"👤 {attendee}")

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">📋 MOM Bot</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Meeting Minutes Generator</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎯 How It Works")
        st.markdown("""
        1. **Upload** your meeting recording
        2. **Wait** for AI to transcribe & analyze
        3. **Get** professional Minutes of Meeting
        4. **Email** to participants

        ### 📊 Supported Formats
        - Audio: MP3, WAV, M4A, WebM
        - Video: MP4, AVI, MOV
        - Any meeting platform
        - Max 2 hours duration
        
        ### 💰 Cost per Meeting
        - ~$0.05 - $0.30
        - Depends on duration
        """)
        
        st.markdown("---")
        
        # Meeting History
        if st.session_state.processed_meetings:
            st.markdown("### 📚 Recent Meetings")
            for meeting in reversed(st.session_state.processed_meetings[-5:]):
                date = datetime.fromisoformat(meeting['date']).strftime("%b %d, %H:%M")
                st.markdown(f"**{meeting['title']}**")
                st.caption(f"📅 {date} • ⏱️ {format_duration(meeting['duration'])}")
                st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Process", "📋 View MOM", "📧 Send Email"])
    
    # Tab 1: Upload & Process
    with tab1:
        st.markdown("### Upload Meeting Recording")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose audio or video file",
                type=['mp3', 'wav', 'm4a', 'webm', 'mp4', 'avi', 'mov'],
                help="Upload your meeting recording (MP3, MP4, WAV, M4A, WebM, AVI, MOV)"
            )
        
        with col2:
            meeting_title = st.text_input(
                "Meeting Title",
                placeholder="e.g., Team Sync - Nov 2025",
                help="Give your meeting a name"
            )
        
        if uploaded_file and meeting_title:
            st.success(f"✅ File uploaded: {uploaded_file.name} ({uploaded_file.size / 1024 / 1024:.2f} MB)")
            
            if st.button("🚀 Process Meeting", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    # Save file
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Process
                    results = process_audio_file(file_path, meeting_title)
                    
                    if results['success']:
                        st.balloons()
                        st.success("🎉 Processing complete! Check the 'View MOM' tab.")
                    else:
                        st.error(f"❌ Error: {results['error']}")
        
        elif uploaded_file and not meeting_title:
            st.warning("⚠️ Please enter a meeting title")
    
    # Tab 2: View MOM
    with tab2:
        if st.session_state.current_mom:
            mom_data = st.session_state.current_mom
            transcript_data = st.session_state.current_transcript
            
            # Stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Duration", format_duration(transcript_data.get('duration', 0)))
            with col2:
                st.metric("Words", f"{len(transcript_data.get('text', '').split()):,}")
            with col3:
                st.metric("Decisions", len(mom_data.get('decisions', [])))
            with col4:
                st.metric("Action Items", len(mom_data.get('action_items', [])))
            
            # Display MOM
            display_mom(mom_data)
            
            # Download buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                mom_json = json.dumps(mom_data, indent=2)
                st.download_button(
                    label="📥 Download MOM (JSON)",
                    data=mom_json,
                    file_name=f"mom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            with col2:
                transcript_text = transcript_data.get('text', '')
                st.download_button(
                    label="📥 Download Transcript (TXT)",
                    data=transcript_text,
                    file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        else:
            st.info("👈 Upload and process a meeting first to see the MOM here")
    
    # Tab 3: Send Email
    with tab3:
        if st.session_state.current_mom:
            st.markdown("### 📧 Email Minutes of Meeting")
            
            # Email form
            with st.form("email_form"):
                recipients = st.text_area(
                    "Recipients",
                    placeholder="Enter email addresses (comma-separated)\ne.g., alice@company.com, bob@company.com",
                    help="Enter one or more email addresses separated by commas"
                )
                
                email_title = st.text_input(
                    "Email Subject",
                    value=f"[MOM] {st.session_state.processed_meetings[-1]['title'] if st.session_state.processed_meetings else 'Meeting'}",
                    help="Subject line for the email"
                )
                
                include_transcript = st.checkbox("Include full transcript", value=False)
                
                submit_button = st.form_submit_button("📨 Send Email", type="primary", use_container_width=True)
                
                if submit_button:
                    if not recipients:
                        st.error("❌ Please enter at least one email address")
                    else:
                        # Parse recipients
                        recipient_list = [email.strip() for email in recipients.split(',')]
                        
                        # Send email
                        with st.spinner("Sending email..."):
                            result = send_mom_email(
                                to_emails=recipient_list,
                                mom_data=st.session_state.current_mom,
                                meeting_title=email_title
                            )
                            
                            if result['status'] == 'success':
                                st.success(f"✅ Email sent successfully to {len(recipient_list)} recipient(s)!")
                                st.balloons()
                            else:
                                st.error(f"❌ Failed to send email: {result['message']}")
        else:
            st.info("👈 Process a meeting first to send emails")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Made with ❤️ by MOM Bot | Powered by OpenAI Whisper & GPT-4</p>
        <p style='font-size: 0.8rem;'>Your meetings deserve better notes 📋</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
