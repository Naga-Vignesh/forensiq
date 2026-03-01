import uuid
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from PIL import Image, ExifTags
import hashlib
import cv2
import numpy as np
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
import math
from dotenv import load_dotenv
import os
from google import genai
from fastapi.staticfiles import StaticFiles
import markdown
import requests
import time
import zipfile

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
# Load AI Authenticity Model (once at startup)
MODEL_NAME = "umm-maybe/AI-image-detector"

processor = AutoImageProcessor.from_pretrained(MODEL_NAME, use_fast=False)
model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
model.eval()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png",".pdf",".zip"}
MAX_FILE_SIZE = 7 * 1024 * 1024  # 5MB limit

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def calculate_entropy(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        if not data:
            return 0

        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1

        entropy = 0
        for count in byte_counts:
            if count == 0:
                continue
            probability = count / len(data)
            entropy -= probability * math.log2(probability)

        return round(entropy, 3)

    except:
        return 0

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def generate_ela_image(original_path):
    original = cv2.imread(original_path)

    # Save temporary compressed version
    temp_path = original_path + "_temp.jpg"
    cv2.imwrite(temp_path, original, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    compressed = cv2.imread(temp_path)

    # Compute difference
    ela_image = cv2.absdiff(original, compressed)

    # Convert to float for dynamic scaling
    ela_float = ela_image.astype(np.float32)

    max_diff = ela_float.max()

    if max_diff == 0:
        max_diff = 1

    # Dynamically scale based on actual max difference
    scale = 255.0 / max_diff
    ela_image = np.clip(ela_float * scale, 0, 255).astype(np.uint8)

    ela_path = original_path + "_ela.jpg"
    cv2.imwrite(ela_path, ela_image)

    return ela_path

def generate_ai_report(forensic_summary, auth_score, risk_level):

    prompt = f"""
You are a professional digital forensic analyst.

Rules:
- Do NOT make definitive accusations.
- Use probability-based language.
- Avoid words like "fake", "criminal", or "malware".
- This is decision-support, not a legal verdict.

Forensic Data:
{forensic_summary}

Authenticity Score: {auth_score}
Risk Level: {risk_level}

Provide:
1. Suspicious indicators
2. Privacy risks
3. Evidence observations
4. Tampering assessment
5. Recommended next steps
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        # Proper safe extraction
        if response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            return "AI explanation unavailable."

    except Exception as e:
        print("Gemini API error:", e)  # TEMP DEBUG
        return "AI explanation temporarily unavailable."
    
def generate_pdf_report(data, output_path):

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Bhama Digital Forensic Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    for key, value in data.items():
        text = f"<b>{key}:</b> {value}"
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))

    doc.build(elements)

def detect_ai_generated(image_path):
    try:
        image = Image.open(image_path).convert("RGB")

        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=1)

        confidence = torch.max(probabilities).item()
        predicted_class = torch.argmax(probabilities).item()

        labels = model.config.id2label
        result_label = labels[predicted_class]

        return {
            "label": result_label,
            "confidence": round(confidence * 100, 2)
        }

    except Exception as e:
        return {
            "label": "Detection Failed",
            "confidence": 0
        }
    
@app.get("/download/{filename}")
def download_file(filename: str):
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if os.path.exists(file_path):
            return FileResponse(
                path=file_path,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=Bhama_Forensic_Report.pdf"
                }
            )

        return HTMLResponse("File not found", status_code=404)
def calculate_authenticity_score(auth_result, exif_data, latitude, longitude, ela_path, width, height,entropy_value,appended_detected,sharpness_value):

    score = 100

    # Metadata consistency
    score -= analyze_metadata_consistency(exif_data)

    # GPS logic
    score -= analyze_gps_logic(latitude, longitude, exif_data)

    synthetic_conf = auth_result["confidence"]
    label = auth_result["label"].lower()
    
    # 1️⃣ Synthetic Probability Handling
    # Even if predicted human, low confidence reduces trust
    if synthetic_conf < 75:
        score -= int((75 - synthetic_conf) * 0.6)

    if "ai" in label:
        score -= int(synthetic_conf * 0.7)

    # 2️⃣ Metadata Integrity
    if not exif_data:
        score -= 25
    else:
        if "Make" not in exif_data:
            score -= 10
        if "Model" not in exif_data:
            score -= 10
        if "DateTimeOriginal" not in exif_data:
            score -= 10

    
    # 3️⃣ GPS Integrity
    if latitude is None or longitude is None:
        score -= 10

    # 5️⃣ AI Typical Resolution Check
    if width in [512, 768, 1024] and height in [512, 768, 1024]:
        score -= 10
    
    # 7️⃣ Appended Data Detection
    if appended_detected:
        score -= 25

    # 6️⃣ Entropy Risk Detection
    if entropy_value > 7.9:
        score -= 15
    elif entropy_value > 7.5:
        score -= 8

    # 8️⃣ Sharpness Evaluation
    if sharpness_value < 50:
        score -= 10  # overly smooth (AI-like)
    elif sharpness_value > 500:
        score -= 5   # abnormal noise
    else:
        score += 5   # healthy natural sharpness

    # 4️⃣ ELA Analysis
    try:
        ela_img = cv2.imread(ela_path)
        mean_intensity = np.mean(ela_img)

        if mean_intensity > 45:
            score -= 20
        elif mean_intensity > 30:
            score -= 10
    except:
        score -= 5

    score = max(score, 0)

    # Risk classification
    if score >= 80:
        risk = "Low Risk (Likely Authentic)"
    elif 50 <= score < 80:
        risk = "Moderate Risk (Requires Review)"
    else:
        risk = "High Risk (Potentially Synthetic or Manipulated)"

    return score, risk

def detect_appended_data(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        # JPEG EOI marker
        eoi_marker = b'\xff\xd9'

        eoi_index = data.rfind(eoi_marker)

        if eoi_index == -1:
            return False, 0

        # Check if anything exists after EOI
        appended_bytes = len(data) - (eoi_index + 2)

        if appended_bytes > 0:
            return True, appended_bytes

        return False, 0

    except:
        return False, 0

def analyze_metadata_consistency(exif_data):
    score_penalty = 0

    camera_fields = ["Make", "Model", "DateTimeOriginal"]

    # 1️⃣ No camera information
    if not any(field in exif_data for field in camera_fields):
        score_penalty += 15

    # 2️⃣ Suspicious software field
    if "Software" in exif_data:
        suspicious_softwares = ["Adobe", "Photoshop", "Stable Diffusion", "Midjourney", "GIMP"]
        if any(word.lower() in exif_data["Software"].lower() for word in suspicious_softwares):
            score_penalty += 20

    return score_penalty

def analyze_gps_logic(latitude, longitude, exif_data):
    penalty = 0

    if latitude and longitude:
        # If GPS exists but no camera make/model → suspicious
        if not ("Make" in exif_data and "Model" in exif_data):
            penalty += 10
    else:
        penalty += 5  # no GPS at all

    return penalty

def calculate_sharpness(image_path):
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        return round(laplacian_var, 2)
    except:
        return 0
    
def query_virustotal(file_hash):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    if not api_key:
        return {"error": "VirusTotal API key not configured."}

    headers = {
        "x-apikey": api_key
    }

    url = f"https://www.virustotal.com/api/v3/files/{file_hash}"

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            stats = data["data"]["attributes"]["last_analysis_stats"]
            return stats
        elif response.status_code == 404:
            return {"info": "File not found in VirusTotal database."}
        else:
            return {"error": f"VT Error: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

def upload_file_to_virustotal(file_path):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    headers = {"x-apikey": api_key}

    url = "https://www.virustotal.com/api/v3/files"

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        analysis_id = response.json()["data"]["id"]
        return analysis_id
    else:
        return None
    
def get_analysis_result(analysis_id):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")
    headers = {"x-apikey": api_key}

    url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"

    for _ in range(10):  # wait up to ~20 seconds
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data["data"]["attributes"]["status"]

            if status == "completed":
                return data["data"]["attributes"]["stats"]

        time.sleep(2)

    return {"error": "Analysis timeout"}

def analyze_zip_file(file_path):

    report = {
        "file_count": 0,
        "suspicious_files": [],
        "total_uncompressed_size": 0,
        "password_protected": False
    }

    try:
        with zipfile.ZipFile(file_path, 'r') as z:

            # Check encryption
            for info in z.infolist():
                report["file_count"] += 1
                report["total_uncompressed_size"] += info.file_size

                if info.flag_bits & 0x1:
                    report["password_protected"] = True

                filename = info.filename.lower()

                suspicious_ext = [".exe", ".js", ".bat", ".ps1", ".vbs", ".scr", ".dll"]

                if any(filename.endswith(ext) for ext in suspicious_ext):
                    report["suspicious_files"].append(filename)

        return report

    except Exception as e:
        return {"error": str(e)}
    
def analyze_zip(request, file_location, original_filename):

    zip_report = analyze_zip_file(file_location)

    md5_hash = hashlib.md5(open(file_location,"rb").read()).hexdigest()
    sha256_hash = hashlib.sha256(open(file_location,"rb").read()).hexdigest()

    vt_result = query_virustotal(sha256_hash)

    if "info" in vt_result:
        analysis_id = upload_file_to_virustotal(file_location)
        if analysis_id:
            vt_result = get_analysis_result(analysis_id)

    return templates.TemplateResponse("zip_report.html", {
        "request": request,
        "filename": original_filename,
        "md5": md5_hash,
        "sha256": sha256_hash,
        "zip_report": zip_report,
        "vt_result": vt_result
    })

@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, file: UploadFile = File(...)):

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        return HTMLResponse("Invalid file type.", status_code=400)

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        return HTMLResponse("File too large. Max size is 7MB.", status_code=400)

    # Save file once
    secure_filename = str(uuid.uuid4()) + file_extension
    file_location = os.path.join(UPLOAD_FOLDER, secure_filename)

    with open(file_location, "wb") as f:
        f.write(content)

    # HANDLE ZIP FIRST
    if file_extension == ".zip":
        return analyze_zip(request, file_location, file.filename)


    # SAVE FILE FIRST
    secure_filename = str(uuid.uuid4()) + file_extension
    file_location = os.path.join(UPLOAD_FOLDER, secure_filename)

    with open(file_location, "wb") as f:
        f.write(content)

    # Generate Hashes
    md5_hash = hashlib.md5(content).hexdigest()
    sha256_hash = hashlib.sha256(content).hexdigest()

    # NOW call VirusTotal
    vt_result = query_virustotal(sha256_hash)

    if "info" in vt_result:
        analysis_id = upload_file_to_virustotal(file_location)
        if analysis_id:
            vt_result = get_analysis_result(analysis_id)

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        return HTMLResponse("File too large. Max size is 5MB.", status_code=400)
    

    # Generate secure random filename
    secure_filename = str(uuid.uuid4()) + file_extension
    file_location = os.path.join(UPLOAD_FOLDER, secure_filename)
    with open(file_location, "wb") as f:
        f.write(content)

    authenticity_result = detect_ai_generated(file_location)

    entropy_value = calculate_entropy(file_location)

    appended_detected, appended_size = detect_appended_data(file_location)

    # Load image safely
    try:
        image = Image.open(file_location)
        width, height = image.size
    except:
        return HTMLResponse("Invalid or corrupted image file.", status_code=400)

    file_extension = os.path.splitext(file.filename)[1].lower()

    if file_extension == ".zip":
        return analyze_zip(request, file_location, file.filename)

    # Default values
    exif_data = {}
    latitude = None
    longitude = None

    # Extract EXIF
    try:
        exif = image._getexif()

        if exif:
            for tag, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag, tag)

                if tag_name in ["Make", "Model", "DateTime", "DateTimeOriginal", "Software", "Orientation"]:
                    exif_data[tag_name] = str(value)

                if tag_name == "GPSInfo":
                    gps_data = value

                    def convert_to_degrees(dms):
                        degrees = dms[0]
                        minutes = dms[1]
                        seconds = dms[2]
                        return degrees + (minutes / 60.0) + (seconds / 3600.0)

                    if 2 in gps_data and 4 in gps_data:
                        lat = convert_to_degrees(gps_data[2])
                        lon = convert_to_degrees(gps_data[4])

                        if gps_data[1] == 'S':
                            lat = -lat
                        if gps_data[3] == 'W':
                            lon = -lon

                        latitude = lat
                        longitude = lon

                        exif_data["Latitude"] = str(latitude)
                        exif_data["Longitude"] = str(longitude)

    except:
        exif_data["info"] = "No readable EXIF metadata."

    # Generate ELA
    ela_path = generate_ela_image(file_location)

    sharpness_value = calculate_sharpness(file_location)

    # Calculate authenticity score
    auth_score, risk_level = calculate_authenticity_score(
        auth_result=authenticity_result,
        exif_data=exif_data,
        latitude=latitude,
        longitude=longitude,
        ela_path=ela_path,
        width=width,
        height=height,
        entropy_value=entropy_value,
        appended_detected=appended_detected,
        sharpness_value=sharpness_value
    )

    # Build forensic summary
    forensic_summary = {
        "Filename": file.filename,
        "MD5": md5_hash,
        "SHA256": sha256_hash,
        "Metadata": exif_data,
        "Latitude": latitude,
        "Longitude": longitude,
        "Authenticity_Label": authenticity_result["label"],
        "Authenticity_Confidence": authenticity_result["confidence"],
        "Authenticity_Score": auth_score,
        "vt_result": vt_result,
        "Risk_Level": risk_level
    }

    # Generate Gemini explanation
    ai_raw_report = generate_ai_report(forensic_summary, auth_score, risk_level)
    ai_report = markdown.markdown(ai_raw_report)

    # Generate PDF report
    pdf_filename = str(uuid.uuid4()) + ".pdf"
    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)

    pdf_data = {
        "Filename": file.filename,
        "MD5": md5_hash,
        "SHA256": sha256_hash,
        "Metadata": exif_data,
        "Latitude": latitude,
        "Longitude": longitude,
        "Authenticity Score": auth_score,
        "Risk Level": risk_level,
        "AI Analysis": ai_report
    }

    generate_pdf_report(pdf_data, pdf_path)

    return templates.TemplateResponse("report.html", {
        "request": request,
        "filename": file.filename,
        "md5": md5_hash,
        "sha256": sha256_hash,
        "exif": exif_data,
        "latitude": latitude,
        "longitude": longitude,
        "ela_image": "/uploads/" + os.path.basename(ela_path),
        "ai_report": ai_report,
        "pdf_file": "/uploads/" + pdf_filename,
        "auth_label": authenticity_result["label"],
        "auth_confidence": authenticity_result["confidence"],
        "auth_score": auth_score,
        "Appended_Data_Detected": appended_detected,
        "Appended_Data_Size_Bytes": appended_size,
        "risk_level": risk_level,
        "vt_result": vt_result,
        "sharpness_value": sharpness_value
    })