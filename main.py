from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import requests

from dotenv import load_dotenv
import google.generativeai as genai


load_dotenv()

app = FastAPI(title="Speech-to-Text API (Gemini)")

const TestAPI = "sk-zzzzzzzzzz"

def get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-pro-latest")
    return genai.GenerativeModel(model_name)


def extract_fields_with_gemini(transcript: str):
    GEMINI_BASE = os.getenv("GEMINI_BASE", "https://generativelanguage.googleapis.com")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    url = f"{GEMINI_BASE}/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    prompt = (
        "You are an assistant that extracts: organization, unit_type, unit, title, "
        "task_type, template, description from this text. Respond in JSON.\n\nText:"\
        f"\n\"{transcript}\""
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    candidates = result.get("candidates", [])
    if not candidates:
        return {}
    text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "{}")
    try:
        import json
        return json.loads(text_out)
    except Exception:
        return {"raw": text_out}


@app.get("/model")
def get_active_model():
    return {"model": get_gemini_model().model_name}


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    content_type = file.content_type or "audio/wav"
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        model = get_gemini_model()
        resp = model.generate_content([
            "Transcribe the following audio to plain text. Return only the transcript.",
            {"mime_type": content_type, "data": data},
        ])
        text = getattr(resp, "text", None)
        if not text:
            raise HTTPException(status_code=502, detail="No text returned by Gemini")
        return JSONResponse({
            "text": text.strip(),
            "model": model.model_name,
            "filename": file.filename,
            "content_type": content_type,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transcribe_and_extract")
async def transcribe_and_extract(file: UploadFile = File(...)):
    content_type = file.content_type or "audio/wav"
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        model = get_gemini_model()
        resp = model.generate_content([
            "Transcribe the following audio to plain text. Return only the transcript.",
            {"mime_type": content_type, "data": data},
        ])
        text = getattr(resp, "text", None)
        if not text:
            raise HTTPException(status_code=502, detail="No text returned by Gemini")
        fields = extract_fields_with_gemini(text.strip())
        return JSONResponse({
            "transcript": text.strip(),
            "fields": fields,
            "model": model.model_name,
            "filename": file.filename,
            "content_type": content_type,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


