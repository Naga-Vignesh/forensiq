🛰️ Forensiq
AI-Powered Digital Image Forensics Platform

Forensiq is a production-grade AI-driven digital image forensic platform designed to analyze image authenticity, detect tampering, extract metadata intelligence, and generate structured forensic reports.

Built with FastAPI, deployed on AWS EC2, secured with Nginx + SSL, and powered by AI + forensic image processing techniques, Forensiq provides a modern, scalable forensic analysis workflow.

🚀 Live Deployment

🌐 Production URL:
https://forensiq.tech

Deployed on:

AWS EC2 (Ubuntu)

Gunicorn (ASGI worker)

Nginx Reverse Proxy

Let’s Encrypt SSL

Custom Domain Configuration

🧠 Core Features
🔍 1. Authenticity Classification

AI-powered image authenticity prediction

Human vs AI-generated detection

Confidence scoring

Visual risk categorization

🧪 2. Tampering Detection (ELA)

Error Level Analysis (ELA) detects image manipulation by:

Recompressing image at controlled JPEG quality

Calculating pixel-level compression differences

Dynamically scaling difference values

Highlighting suspicious compression artifacts

✔ Dynamic ELA amplification
✔ Tampering visibility enhancement
✔ Optional heatmap forensic mode

🔐 3. Cryptographic Integrity

MD5 hash generation

SHA256 hash generation

Chain-of-custody verification support

🦠 4. VirusTotal Threat Intelligence

File hash scanning via VirusTotal API

Malicious / Suspicious / Undetected breakdown

Real-time threat classification panel

📍 5. Metadata Intelligence

EXIF extraction

Camera data

Device information

Timestamp analysis

Embedded GPS coordinates

If GPS metadata exists:

Direct Google Maps link generation

🤖 6. AI Forensic Report

Natural-language AI-generated forensic summary

Structured risk interpretation

Professional investigative tone

Powered by:

Google Gemini API (rate-limited with fail-safe handling)

🏗️ Architecture Overview
Backend

FastAPI

Uvicorn

Gunicorn (UvicornWorker)

Python 3.11

Frontend

Jinja2 Templates

Bootstrap 5

Custom dark forensic UI theme

Infrastructure

AWS EC2 (Ubuntu)

Nginx reverse proxy

Let’s Encrypt SSL

systemd service management

Security Controls

HTTPS enforced

Reverse proxy isolation

API quota protection

Worker timeout configuration

Rate limiting (IP-based)

Gunicorn max-request cycling

📦 Installation (Local Development)
git clone https://github.com/Naga-Vignesh/forensiq.git
cd forensiq

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

Run locally:

uvicorn main:app --reload
⚙️ Production Deployment

Gunicorn:

gunicorn -k uvicorn.workers.UvicornWorker main:app \
--bind 127.0.0.1:8000 \
--workers 2 \
--timeout 120

Nginx Reverse Proxy:

server {
    listen 80;
    server_name forensiq.tech www.forensiq.tech;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

SSL Setup:

sudo certbot --nginx -d forensiq.tech -d www.forensiq.tech
📊 ELA Algorithm (Dynamic Scaling Implementation)

Instead of fixed amplification, Forensiq uses adaptive scaling:

ela_image = cv2.absdiff(original, compressed)
ela_float = ela_image.astype(np.float32)

max_diff = ela_float.max()
if max_diff == 0:
    max_diff = 1

scale = 255.0 / max_diff
ela_image = np.clip(ela_float * scale, 0, 255).astype(np.uint8)

This ensures:

Subtle manipulations remain visible

Brightest anomaly is fully scaled

Accurate forensic representation

🔐 API Key Configuration

Environment variables required:

GOOGLE_API_KEY=your_gemini_key
VT_API_KEY=your_virustotal_key

Set securely:

export GOOGLE_API_KEY=...
export VT_API_KEY=...
🛡️ Production Safeguards

✔ Gemini 429 quota lock handling
✔ Graceful failure messaging
✔ Gunicorn worker timeout protection
✔ Rate limiting to prevent API abuse
✔ File size restrictions (Nginx 413 protection)

🧠 Challenges Faced & Lessons Learned

Building and deploying Forensiq was not just about writing code — it involved solving real-world infrastructure, AI integration, and production deployment challenges.

1️⃣ AI API Quota Exhaustion (Gemini 429 Errors)
Problem

While deploying to production, the Gemini API began returning:

429 RESOURCE_EXHAUSTED
Quota exceeded for metric: generate_content_free_tier_requests

The free-tier limit (20 requests/day per model) was quickly exceeded during testing.

Impact

Worker timeouts in Gunicorn

Repeated API failures

Log flooding

Unstable production behavior

Solution

Implemented graceful exception handling for ResourceExhausted

Added quota lock mechanism to prevent repeated API calls after exhaustion

Added request rate limiting to prevent abuse

Configured Gunicorn timeout properly

Designed fail-fast fallback messaging for users

Lesson Learned

AI APIs must always be integrated with:

Quota awareness

Fail-safe handling

Rate limiting

Cost-control strategy

Never assume external AI services are infinite.

2️⃣ Gunicorn Worker Timeouts
Problem

Long-running AI calls caused:

CRITICAL WORKER TIMEOUT
Worker was sent SIGABRT
Root Cause

Blocking API calls

Default Gunicorn timeout too low

No proper background handling

Solution

Increased Gunicorn timeout (--timeout 120)

Optimized API error handling

Added controlled retry logic

Configured worker recycling (--max-requests)

Lesson Learned

Production deployments require:

Proper worker configuration

Non-blocking request strategies

Defensive timeout settings

3️⃣ Nginx 413 Request Entity Too Large
Problem

Uploading large images resulted in:

413 Request Entity Too Large
Solution

Added:

client_max_body_size 20M;

Restarted Nginx.

Lesson Learned

Reverse proxies enforce upload limits.
Backend configuration alone is not enough.

4️⃣ ELA Image Visibility Issues
Problem

Initial Error Level Analysis images appeared nearly black and unreadable.

Root Cause

Fixed amplification multiplier (×10) was insufficient.

Solution

Implemented dynamic pixel scaling:

max_diff = ela_float.max()
scale = 255.0 / max_diff

This ensured:

Brightest anomaly scales to white

Subtle compression differences remain visible

Lesson Learned

Forensic visualization requires adaptive scaling, not fixed amplification.

📈 Future Roadmap

Redis caching for AI responses

S3 storage integration

Load balancer scaling

User authentication system

Usage analytics dashboard

Stripe billing tier

AI tampering region bounding boxes

Heatmap forensic visualization

🧑‍💻 Author

Naga Vignesh
Cybersecurity & AI Systems Engineer

GitHub: https://github.com/Naga-Vignesh

📜 License

MIT License

🧾 Technical Summary

Forensiq demonstrates:

Full-stack deployment capability

AI integration with rate-limit handling

Secure reverse-proxy architecture

Forensic image processing

Cloud production infrastructure

Defensive API consumption strategies

Secure domain and SSL configuration
