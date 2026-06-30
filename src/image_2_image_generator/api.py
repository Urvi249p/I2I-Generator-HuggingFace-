import os
import sys
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from image_2_image_generator.marketing_flow import MarketingPosterFlow

load_dotenv()

app = FastAPI(
    title="AI Image to Poster API",
    description="Transform any image into a marketing poster using WaveSpeed AI",
    version="1.0.0",
)

# Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request & Response Models ---
class GenerateRequest(BaseModel):
    image_url: str
    object_description: str
    poster_prompt: str = ""
    quality: str = "high"
    resolution: str = "2k"


class GenerateResponse(BaseModel):
    success: bool
    result_url: str = ""
    error: str = ""
    job_id: str = ""


# --- Helper ---
def extract_drive_url(drive_link: str) -> str:
    """Convert any Google Drive share link to a direct download URL."""
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/open\?id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, drive_link)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return drive_link


# --- Routes ---
@app.get("/")
def root():
    return {"message": "AI Image to Poster API is running 🎨"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate_poster(request: GenerateRequest):
    # Convert Drive link if needed
    image_url = extract_drive_url(request.image_url)

    # Run the flow
    try:
        flow = MarketingPosterFlow()
        flow.kickoff(inputs={
            "image_url": image_url,
            "object_description": request.object_description,
            "poster_prompt": request.poster_prompt,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if flow.state.result_url:
        return GenerateResponse(
            success=True,
            result_url=flow.state.result_url,
            job_id=flow.state.job_id,
        )
    else:
        return GenerateResponse(
            success=False,
            error=flow.state.error,
        )