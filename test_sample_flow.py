"""Quick test of sample meeting flow"""

from generate_mom import generate_mom
from email_service import send_mom_email

print("🧪 Testing Sample 9-Minute Meeting Flow\n")

# Generate MOM
print("📍 Step 1: Generating MOM...")
mom = generate_mom('sample_9min_transcript.json')

if mom:
    print("✅ MOM generated successfully!\n")
    
    # Ask about email
    send = input("Send test email? (y/n): ").strip().lower()
    
    if send == 'y':
        email = input("Enter your email: ").strip()
        if email:
            result = send_mom_email(email, mom, "Q1 Marketing Campaign Planning")
            if result['status'] == 'success':
                print("\n✅ Email sent! Check your inbox.")
            else:
                print(f"\n❌ Error: {result['message']}")
else:
    print("❌ MOM generation failed")
