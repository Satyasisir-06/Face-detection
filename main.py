"""
AURA Vision — Vercel-compatible FastAPI entrypoint.

This is a lightweight API surface deployed on Vercel.
The full real-time vision pipeline (webcam, DeepFace, OpenCV) requires
a local or VM deployment — see README.md for instructions.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import time

app = FastAPI(
    title="AURA Vision — AI Face Detection & Analysis API",
    description="Real-time Age, Gender & Emotion detection system. "
                "Deploy locally with `python run.py` for full webcam + DeepFace pipeline.",
    version="1.0.0",
)


@app.get("/")
async def root():
    return {
        "project": "AURA Vision",
        "description": "AI-powered Age, Gender & Emotion Detection System",
        "status": "online",
        "endpoints": {
            "/": "This overview",
            "/api/status": "System health and capability check",
            "/api/info": "Full project information and architecture",
        },
        "note": "For live webcam streaming with DeepFace analysis, run locally: python run.py",
    }


@app.get("/api/status")
async def get_status():
    """Return system status and detected capabilities."""
    deepface_available = False
    opencv_available = False

    try:
        import cv2  # noqa: F401
        opencv_available = True
    except ImportError:
        pass

    try:
        from deepface import DeepFace  # noqa: F401
        deepface_available = True
    except ImportError:
        pass

    return {
        "status": "online",
        "opencv_available": opencv_available,
        "deepface_available": deepface_available,
        "timestamp": time.time(),
        "deploy_mode": "vercel-serverless",
        "note": "Full real-time pipeline available when running locally via python run.py",
    }


@app.get("/api/info")
async def get_info():
    """Return full project architecture and capabilities."""
    return {
        "project": "AURA Vision",
        "version": "1.0.0",
        "architecture": {
            "backend": "FastAPI + Uvicorn",
            "vision_engine": "OpenCV Haar Cascade + DeepFace (ArcFace/FaceNet)",
            "streaming": "WebSocket real-time at 25 FPS",
            "frontend": "HTML5 Canvas + Glassmorphism UI",
        },
        "capabilities": {
            "face_detection": "OpenCV Haar Cascade with 25% ROI padding",
            "age_prediction": "DeepFace neural network",
            "gender_classification": "30-frame sliding window majority latching",
            "emotion_analysis": "7-class (Happy, Neutral, Sad, Angry, Surprise, Fear, Disgust)",
            "smoothing": "Exponential Moving Average (alpha=0.25)",
        },
        "future_upgrades": {
            "layer_1": "Multi-camera RTSP/IP stream ingestion",
            "layer_2": "512D facial embedding extraction (ArcFace/FaceNet)",
            "layer_3": "Vector database suspect matching (Milvus/FAISS)",
            "layer_4": "SIEM integration & real-time alerting",
            "layer_5": "Anti-spoofing, liveness detection & encryption",
        },
        "industries": [
            "Cybersecurity — physical-to-cyber access correlation",
            "Banking — ATM fraud & skimming prevention",
            "Retail — shoplifting & repeat offender alerts",
            "Smart Cities — BOLO networks at transit hubs",
            "Access Control — server room & data center security",
        ],
        "local_run": "python run.py  (full webcam + DeepFace pipeline)",
        "repository": "https://github.com/Satyasisir-06/Face-detection",
    }
