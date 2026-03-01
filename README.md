# 🛰️ Forensiq

**AI-Powered Digital Image Forensics Platform**

Forensiq is a production-grade digital image forensic platform that analyzes image authenticity, detects manipulation, extracts metadata intelligence, and generates structured forensic reports.

Built with **FastAPI**, deployed on **AWS EC2**, secured with **Nginx + SSL**, and powered by **AI + forensic image processing techniques**, Forensiq offers a scalable and modern forensic workflow.

---

## 🚀 Live Deployment

### 🌐 Production URL

- https://forensiq.tech

### Deployment Stack

- AWS EC2 (Ubuntu)
- Gunicorn (ASGI worker)
- Nginx reverse proxy
- Let’s Encrypt SSL
- Custom domain configuration

---

## 🧠 Core Features

### 1) 🔍 Authenticity Classification

- AI-powered image authenticity prediction
- Human vs AI-generated detection
- Confidence scoring
- Visual risk categorization

### 2) 🧪 Tampering Detection (ELA)

Error Level Analysis (ELA) detects manipulation by:

- Recompressing image at controlled JPEG quality
- Calculating pixel-level compression differences
- Dynamically scaling difference values
- Highlighting suspicious compression artifacts

Additional capabilities:

- Dynamic ELA amplification
- Tampering visibility enhancement
- Optional heatmap forensic mode

### 3) 🔐 Cryptographic Integrity

- MD5 hash generation
- SHA256 hash generation
- Chain-of-custody verification support

### 4) 🦠 VirusTotal Threat Intelligence

- File hash scanning via VirusTotal API
- Malicious / Suspicious / Undetected breakdown
- Real-time threat classification panel

### 5) 📍 Metadata Intelligence

- EXIF extraction
- Camera/device information
- Timestamp analysis
- Embedded GPS coordinate parsing

If GPS metadata exists, Forensiq can generate direct Google Maps links.

### 6) 🤖 AI Forensic Report

- Natural-language AI-generated forensic summary
- Structured risk interpretation
- Professional investigative tone

Powered by Google Gemini API with rate-limited fail-safe handling.

---

## 🏗️ Architecture Overview

### Backend

- FastAPI
- Uvicorn
- Gunicorn (UvicornWorker)
- Python 3.11

### Frontend

- Jinja2 templates
- Bootstrap 5
- Custom dark forensic UI theme

### Infrastructure

- AWS EC2 (Ubuntu)
- Nginx reverse proxy
- Let’s Encrypt SSL
- systemd service management

### Security Controls

- HTTPS enforced
- Reverse proxy isolation
- API quota protection
- Worker timeout configuration
- IP-based rate limiting
- Gunicorn max-request cycling

---

## 📦 Installation (Local Development)

```bash
git clone https://github.com/Naga-Vignesh/forensiq.git
cd forensiq

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run locally:

```bash
uvicorn main:app --reload
```

---

## ⚙️ Production Deployment

### Gunicorn

```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app \
  --bind 127.0.0.1:8000 \
  --workers 2 \
  --timeout 120
```

### Nginx Reverse Proxy (example)

```nginx
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
```

### SSL Setup

```bash
sudo certbot --nginx -d forensiq.tech -d www.forensiq.tech
```

---

## 📊 ELA Algorithm (Dynamic Scaling)

Forensiq uses adaptive scaling instead of fixed amplification:

```python
ela_image = cv2.absdiff(original, compressed)
ela_float = ela_image.astype(np.float32)

max_diff = ela_float.max()
if max_diff == 0:
    max_diff = 1

scale = 255.0 / max_diff
ela_image = np.clip(ela_float * scale, 0, 255).astype(np.uint8)
```

Benefits:

- Subtle manipulations remain visible
- Brightest anomalies are fully scaled
- More accurate forensic visualization

---

## 🔐 API Key Configuration

Required environment variables:

```bash
GOOGLE_API_KEY=your_gemini_key
VT_API_KEY=your_virustotal_key
```

Set securely:

```bash
export GOOGLE_API_KEY=...
export VT_API_KEY=...
```

---

## 🛡️ Production Safeguards

- Gemini 429 quota lock handling
- Graceful failure messaging
- Gunicorn worker timeout protection
- Rate limiting to reduce abuse
- File size restrictions (e.g., Nginx 413 protection)

---

## 🧠 Challenges & Lessons Learned

### 1) AI API Quota Exhaustion (Gemini 429)

**Problem**

Free-tier Gemini quota was exceeded during testing (`RESOURCE_EXHAUSTED`).

**Impact**

- Worker timeouts
- Repeated API failures
- Log flooding

**Solution**

- Graceful exception handling for quota errors
- Quota lock to prevent repeated failing calls
- Request rate limiting
- Fail-fast fallback messaging

**Lesson**

External AI services require quota awareness, fail-safes, and defensive rate controls.

### 2) Gunicorn Worker Timeouts

**Problem**

Long-running AI calls caused worker aborts and timeout errors.

**Solution**

- Increased timeout (`--timeout 120`)
- Improved API error handling
- Added controlled retry logic
- Enabled worker recycling (`--max-requests`)

**Lesson**

Production services need defensive timeout and worker lifecycle tuning.

### 3) Nginx 413 Request Entity Too Large

**Problem**

Large uploads triggered `413 Request Entity Too Large`.

**Solution**

Set Nginx upload limit:

```nginx
client_max_body_size 20M;
```

**Lesson**

Proxy-layer upload limits must be configured explicitly.

### 4) ELA Visibility Issues

**Problem**

Early ELA outputs were too dark to interpret.

**Solution**

Implemented adaptive scaling based on maximum observed difference.

**Lesson**

Forensic visualization quality depends on dynamic scaling, not fixed multipliers.

---

## 📈 Future Roadmap

- Redis caching for AI responses
- S3 storage integration
- Load balancer scaling
- User authentication
- Usage analytics dashboard
- Stripe billing tiers
- AI tampering region bounding boxes
- Enhanced heatmap visualization

---

## 🧑‍💻 Author

**Naga Vignesh**  
Cybersecurity & AI Systems Engineer

- GitHub: https://github.com/Naga-Vignesh

---

## 📜 License

MIT License

---

## 🧾 Technical Summary

Forensiq demonstrates:

- Full-stack deployment capability
- AI integration with quota/rate-limit handling
- Secure reverse-proxy architecture
- Forensic image processing pipeline
- Cloud production infrastructure
- Defensive external API consumption
- Secure domain and SSL configuration
