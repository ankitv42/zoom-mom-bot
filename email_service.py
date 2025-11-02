"""
Email service to send MOM to participants using SendGrid
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "MOM Bot")

def create_mom_html(mom_data):
    """
    Create beautiful HTML email from MOM data
    
    Args:
        mom_data: Dictionary containing MOM information
    
    Returns:
        str: HTML formatted email
    """
    
    # Extract data
    summary = mom_data.get('summary', 'No summary available')
    key_points = mom_data.get('key_points', [])
    decisions = mom_data.get('decisions', [])
    action_items = mom_data.get('action_items', [])
    questions = mom_data.get('questions', [])
    next_steps = mom_data.get('next_steps', 'No next steps specified')
    attendees = mom_data.get('attendees', [])
    metadata = mom_data.get('metadata', {})
    
    # Get meeting date
    generated_at = metadata.get('generated_at', datetime.now().isoformat())
    meeting_date = generated_at.split('T')[0]
    
    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px 8px 0 0;
                margin: -30px -30px 30px -30px;
            }}
            h1 {{
                margin: 0;
                font-size: 24px;
            }}
            .meta {{
                font-size: 14px;
                color: rgba(255,255,255,0.9);
                margin-top: 8px;
            }}
            h2 {{
                color: #667eea;
                border-bottom: 2px solid #667eea;
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            .summary {{
                background-color: #f8f9ff;
                padding: 15px;
                border-left: 4px solid #667eea;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .item {{
                background-color: #fff;
                border: 1px solid #e0e0e0;
                padding: 12px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .item-header {{
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }}
            .item-detail {{
                color: #666;
                font-size: 14px;
                margin-left: 20px;
            }}
            .decision {{
                border-left: 4px solid #10b981;
            }}
            .action {{
                border-left: 4px solid #f59e0b;
            }}
            .question {{
                border-left: 4px solid #ef4444;
            }}
            .priority-high {{
                color: #ef4444;
                font-weight: bold;
            }}
            .priority-medium {{
                color: #f59e0b;
            }}
            .priority-low {{
                color: #10b981;
            }}
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
            ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .attendees {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin: 15px 0;
            }}
            .attendee {{
                background-color: #f0f0f0;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 Minutes of Meeting</h1>
                <div class="meta">Generated on {meeting_date}</div>
            </div>
    """
    
    # Attendees
    if attendees:
        html += """
            <h2>👥 Attendees</h2>
            <div class="attendees">
        """
        for attendee in attendees:
            html += f'<div class="attendee">{attendee}</div>'
        html += "</div>"
    
    # Summary
    html += f"""
            <h2>📝 Summary</h2>
            <div class="summary">
                {summary}
            </div>
    """
    
    # Key Points
    if key_points:
        html += """
            <h2>🔑 Key Discussion Points</h2>
            <ul>
        """
        for point in key_points:
            html += f"<li>{point}</li>"
        html += "</ul>"
    
    # Decisions
    if decisions:
        html += """
            <h2>✅ Decisions Made</h2>
        """
        for i, decision in enumerate(decisions, 1):
            made_by = decision.get('made_by', 'Team')
            timestamp = decision.get('timestamp', '')
            html += f"""
            <div class="item decision">
                <div class="item-header">{i}. {decision.get('decision', 'N/A')}</div>
                <div class="item-detail">👤 Decided by: {made_by}</div>
            """
            if timestamp:
                html += f'<div class="item-detail">🕐 Time: {timestamp}</div>'
            html += "</div>"
    
    # Action Items
    if action_items:
        html += """
            <h2>📌 Action Items</h2>
        """
        for i, item in enumerate(action_items, 1):
            owner = item.get('owner', 'Unassigned')
            deadline = item.get('deadline', 'Not specified')
            priority = item.get('priority', 'medium')
            priority_class = f"priority-{priority}"
            
            html += f"""
            <div class="item action">
                <div class="item-header">{i}. {item.get('task', 'N/A')}</div>
                <div class="item-detail">👤 Owner: {owner}</div>
                <div class="item-detail">📅 Deadline: {deadline}</div>
                <div class="item-detail">⚡ Priority: <span class="{priority_class}">{priority.upper()}</span></div>
            </div>
            """
    
    # Questions
    if questions:
        html += """
            <h2>❓ Open Questions</h2>
        """
        for i, question in enumerate(questions, 1):
            html += f"""
            <div class="item question">
                <div class="item-header">{i}. {question}</div>
            </div>
            """
    
    # Next Steps
    if next_steps and next_steps != "No next steps specified":
        html += f"""
            <h2>🚀 Next Steps</h2>
            <div class="summary">
                {next_steps}
            </div>
        """
    
    # Footer
    html += """
            <div class="footer">
                <p>This MOM was automatically generated by MOM Bot 🤖</p>
                <p>Powered by AI • Generated with GPT-4 & Whisper</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_mom_email(to_emails, mom_data, meeting_title="Team Meeting"):
    """
    Send MOM via email to participants
    
    Args:
        to_emails: List of recipient emails or single email string
        mom_data: Dictionary containing MOM data
        meeting_title: Title of the meeting
    
    Returns:
        dict: Status of email sending
    """
    
    # Validate API key
    if not SENDGRID_API_KEY:
        print("❌ Error: SENDGRID_API_KEY not found in .env file")
        return {"status": "error", "message": "API key not configured"}
    
    if not SENDGRID_FROM_EMAIL:
        print("❌ Error: SENDGRID_FROM_EMAIL not found in .env file")
        return {"status": "error", "message": "From email not configured"}
    
    # Convert single email to list
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    # Create HTML content
    html_content = create_mom_html(mom_data)
    
    # Create plain text version (fallback)
    summary = mom_data.get('summary', 'No summary available')
    plain_text = f"Minutes of Meeting: {meeting_title}\n\n"
    plain_text += f"Summary:\n{summary}\n\n"
    plain_text += "Please view this email in HTML format for the full formatted MOM.\n"
    
    # Email subject
    meeting_date = datetime.now().strftime("%Y-%m-%d")
    subject = f"[MOM] {meeting_title} - {meeting_date}"
    
    print(f"📧 Preparing to send email...")
    print(f"   From: {SENDGRID_FROM_NAME} <{SENDGRID_FROM_EMAIL}>")
    print(f"   To: {', '.join(to_emails)}")
    print(f"   Subject: {subject}")
    
    try:
        # Create SendGrid client
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        
        # Create message
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=[To(email) for email in to_emails],
            subject=subject,
            plain_text_content=Content("text/plain", plain_text),
            html_content=Content("text/html", html_content)
        )
        
        # Send email
        response = sg.send(message)
        
        print(f"✅ Email sent successfully!")
        print(f"   Status code: {response.status_code}")
        
        return {
            "status": "success",
            "status_code": response.status_code,
            "recipients": to_emails,
            "message": "Email sent successfully"
        }
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    # Test with sample MOM data
    print("🧪 Testing email service...\n")
    
    # Check if MOM file exists
    mom_file = "test_meeting_mom.json"
    
    if not os.path.exists(mom_file):
        print(f"❌ Error: {mom_file} not found!")
        print("Please run generate_mom.py first to create a MOM")
    else:
        # Load MOM data
        with open(mom_file, 'r') as f:
            mom_data = json.load(f)
        
        # Get recipient email
        print("📧 Email Test")
        print("="*60)
        recipient = input("Enter your email address to receive test MOM: ").strip()
        
        if not recipient:
            print("❌ No email provided. Using default from .env")
            recipient = SENDGRID_FROM_EMAIL
        
        # Send email
        result = send_mom_email(
            to_emails=recipient,
            mom_data=mom_data,
            meeting_title="Test Meeting - Q4 Planning"
        )
        
        if result["status"] == "success":
            print("\n✅ TEST SUCCESSFUL!")
            print(f"   Check your inbox: {recipient}")
            print("   (Check spam folder if not in inbox)")
        else:
            print(f"\n❌ TEST FAILED: {result['message']}")
