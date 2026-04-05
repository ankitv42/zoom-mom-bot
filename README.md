# AI Meeting Intelligence Agent

> Automatically transcribes meeting audio/video, generates structured Minutes of Meeting (MOM) using GPT-4o-mini, and emails them to participants.
>
> ## What It Does
>
> Upload a Zoom (or any) meeting recording and this agent will:
>
> 1. **Transcribe** the audio using OpenAI Whisper
> 2. 2. **Analyse** the transcript with GPT-4o-mini via the OpenAI API
>    3. 3. **Generate** a structured MOM containing:
>       4.    - Meeting summary
>             -    - Key decisions made
>                  -    - Action items with owners
>                       - 4. **Email** the MOM to participants via SendGrid
>                        
>                         5. ## Tech Stack
>                        
>                         6. | Layer | Technology |
>                         7. |---|---|
>                         8. | Frontend | Streamlit |
> | AI / Transcription | OpenAI Whisper, GPT-4o-mini |
> | Email | SendGrid |
> | Containerisation | Docker |
> | Language | Python 3.11 |
>
> ## Project Structure
>
> ```
> zoom-mom-bot/
> ├── app/                  # Streamlit UI modules
> ├── app.py                # Main application entry point
> ├── transcribe_audio.py   # Whisper transcription logic
> ├── generate_mom.py       # GPT-4o-mini MOM generation (response_format: json_object)
> ├── process_meeting.py    # Core pipeline orchestration
> ├── process_long_meeting.py  # Chunked processing for long recordings
> ├── email_service.py      # SendGrid email delivery
> ├── Dockerfile            # Container definition
> └── requirements.txt      # Python dependencies
> ```
>
> ## Setup
>
> ### Prerequisites
>
> - Python 3.11+
> - - Docker (optional)
>   - - OpenAI API key
>     - - SendGrid API key
>      
>       - ### Local Development
>      
>       - ```bash
>         # Clone the repo
>         git clone https://github.com/ankitv42/zoom-mom-bot.git
>         cd zoom-mom-bot
>
>         # Install dependencies
>         pip install -r requirements.txt
>
>         # Set environment variables
>         export OPENAI_API_KEY=your_openai_key
>         export SENDGRID_API_KEY=your_sendgrid_key
>         export SENDER_EMAIL=your_verified_sender@example.com
>
>         # Run the app
>         streamlit run app.py
>         ```
>
> ### Docker
>
> ```bash
> docker build -t ai-meeting-agent .
> docker run -p 8501:8501 \
>   -e OPENAI_API_KEY=your_openai_key \
>   -e SENDGRID_API_KEY=your_sendgrid_key \
>   ai-meeting-agent
> ```
>
> Then open `http://localhost:8501`.
>
> ## Key Implementation Details
>
> - Uses `response_format: json_object` with the OpenAI Chat Completions API for reliable structured output
> - - Long recordings are split into chunks and processed sequentially to stay within token limits
>   - - Supports both audio (`.mp3`, `.wav`) and video (`.mp4`) uploads
>     - - Dockerised and deployable to Railway, Render, or any container platform
>      
>       - ## Environment Variables
>      
>       - | Variable | Description |
>       - |---|---|
>       - | `OPENAI_API_KEY` | Your OpenAI API key |
> | `SENDGRID_API_KEY` | Your SendGrid API key |
> | `SENDER_EMAIL` | Verified sender email address |
> | `PORT` | App port (default: 8501) |
