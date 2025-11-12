FROM python:3.10.12-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create directories
RUN mkdir -p uploads transcripts moms

# Let Railway provide PORT dynamically
EXPOSE 8501

# ✅ Neutralize the bad environment variable before launching Streamlit
CMD ["bash", "-c", "unset STREAMLIT_SERVER_PORT && streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
