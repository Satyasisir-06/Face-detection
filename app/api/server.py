import asyncio
import base64
import os
import time
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import numpy as np
import cv2

from app.vision.camera_stream import CameraStream
from app.vision.face_detector import FaceDetector
from app.vision.analyzer import FaceAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceRecogAPI")

app = FastAPI(
    title="AURA Vision - Suspect Identification & Face Analysis Engine",
    description="Real-time Criminal & Suspect Watchlist Interception, Face Recognition & Demographic Analytics",
    version="2.0.0"
)

# Enable CORS for local web interfaces and cross-origin access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Vision Engine Instances
# Default to -1 so Python does not lock the webcam hardware device on Windows,
# allowing the browser full, non-conflicting access.
camera_id = int(os.environ.get("CAMERA_DEVICE_ID", "-1"))
camera = CameraStream(camera_id=camera_id, fps=30)
detector = FaceDetector(min_confidence=0.5)
analyzer = FaceAnalyzer(use_deepface=True)

@app.on_event("startup")
async def startup_event():
    camera.start()
    logger.info("Vision pipeline and camera server started.")

@app.on_event("shutdown")
async def shutdown_event():
    camera.stop()
    logger.info("Camera stream closed.")

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "system": "AURA Vision Watchlist & Face Recognition",
        "real_camera": camera.is_real_camera,
        "deepface_loaded": analyzer.deepface_available,
        "enrolled_members_count": len(analyzer.enrolled_faces),
        "suspects_count": sum(1 for m in analyzer.enrolled_faces if m.get("is_suspect")),
        "fps_target": camera.fps,
        "timestamp": time.time()
    }

@app.get("/api/members")
async def get_members():
    """Return enrolled watchlist members (suspects and authorized personnel)."""
    return {
        "count": len(analyzer.enrolled_faces),
        "suspects_count": sum(1 for m in analyzer.enrolled_faces if m.get("is_suspect")),
        "members_count": sum(1 for m in analyzer.enrolled_faces if not m.get("is_suspect")),
        "members": [
            {
                "id": m["id"],
                "name": m["name"],
                "full_name": m.get("full_name", m["name"]),
                "is_suspect": m.get("is_suspect", False),
                "threat_level": m.get("threat_level", "NONE"),
                "status": m.get("status", "Active"),
                "category": m.get("category", "Member"),
                "image_url": m.get("image_url", f"/members/{m['id']}.jpeg"),
                "badge": m.get("badge", "MEMBER")
            }
            for m in analyzer.enrolled_faces
        ]
    }

@app.post("/api/identify")
async def identify_image(payload: dict = Body(...)):
    """
    Identify faces and detect suspects in an uploaded base64 image frame.
    Supports live testing of member photos and security surveillance snapshots.
    """
    image_b64 = payload.get("image", "")
    if not image_b64:
        raise HTTPException(status_code=400, detail="Missing 'image' key with base64 data")

    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    try:
        raw_bytes = base64.b64decode(image_b64)
        np_arr = np.frombuffer(raw_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Decoded image is empty or invalid format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Image decoding failed: {e}")

    faces = detector.detect_faces(frame)
    analysis_results = []
    suspect_detected = False

    for idx, f in enumerate(faces):
        face_id = f"test_face_{idx}"
        analysis = analyzer.analyze_crop(f['crop'], face_id=face_id)
        if analysis.get("is_suspect"):
            suspect_detected = True

        analysis_results.append({
            "id": face_id,
            "box": {"x": f['x'], "y": f['y'], "w": f['w'], "h": f['h']},
            "confidence": f['confidence'],
            "identity": analysis.get('identity', 'Visitor'),
            "full_name": analysis.get('full_name', 'Visitor'),
            "is_suspect": analysis.get('is_suspect', False),
            "threat_level": analysis.get('threat_level', 'NONE'),
            "status": analysis.get('status', 'Unregistered Visitor'),
            "badge": analysis.get('badge', '👤 VISITOR'),
            "match_confidence": analysis.get('match_confidence', 0.0),
            "age": analysis['age'],
            "gender": analysis['gender'],
            "gender_confidence": analysis['gender_confidence'],
            "emotion": analysis['emotion'],
            "emotion_confidence": analysis['emotion_confidence'],
            "emotions_distribution": analysis['emotions_distribution']
        })

    return {
        "status": "success",
        "faces_detected": len(faces),
        "suspect_alert": suspect_detected,
        "faces": analysis_results,
        "timestamp": time.time()
    }

@app.get("/api/snapshot")
async def get_snapshot():
    frame = camera.get_frame()
    if frame is None:
        return JSONResponse(status_code=500, content={"error": "No frame available"})

    faces = detector.detect_faces(frame)
    analysis_results = []
    suspect_detected = False

    for idx, f in enumerate(faces):
        face_id = f"face_{idx}"
        analysis = analyzer.analyze_crop(f['crop'], face_id=face_id)
        if analysis.get("is_suspect"):
            suspect_detected = True

        analysis_results.append({
            "id": face_id,
            "box": {"x": f['x'], "y": f['y'], "w": f['w'], "h": f['h']},
            "confidence": f['confidence'],
            "identity": analysis.get('identity', 'Visitor'),
            "full_name": analysis.get('full_name', 'Visitor'),
            "is_suspect": analysis.get('is_suspect', False),
            "threat_level": analysis.get('threat_level', 'NONE'),
            "status": analysis.get('status', 'Unregistered Visitor'),
            "badge": analysis.get('badge', '👤 VISITOR'),
            "match_confidence": analysis.get('match_confidence', 0.0),
            "age": analysis['age'],
            "gender": analysis['gender'],
            "gender_confidence": analysis['gender_confidence'],
            "emotion": analysis['emotion'],
            "emotion_confidence": analysis['emotion_confidence'],
            "emotions_distribution": analysis['emotions_distribution']
        })

    frame_base64 = camera.get_jpeg_base64(frame, quality=90)
    return {
        "frame_base64": frame_base64,
        "suspect_alert": suspect_detected,
        "faces": analysis_results,
        "timestamp": time.time()
    }

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected to WebSocket stream.")
    
    fps = 25
    interval = 1.0 / fps

    try:
        while True:
            t0 = time.time()
            frame = camera.get_frame()

            if frame is not None:
                faces = detector.detect_faces(frame)
                analysis_results = []
                suspect_detected = False

                for idx, f in enumerate(faces):
                    face_id = f"face_{idx}"
                    analysis = analyzer.analyze_crop(f['crop'], face_id=face_id)
                    if analysis.get("is_suspect"):
                        suspect_detected = True

                    analysis_results.append({
                        "id": face_id,
                        "box": {"x": f['x'], "y": f['y'], "w": f['w'], "h": f['h']},
                        "identity": analysis.get('identity', 'Visitor'),
                        "full_name": analysis.get('full_name', 'Visitor'),
                        "is_suspect": analysis.get('is_suspect', False),
                        "threat_level": analysis.get('threat_level', 'NONE'),
                        "status": analysis.get('status', 'Unregistered Visitor'),
                        "badge": analysis.get('badge', '👤 VISITOR'),
                        "match_confidence": analysis.get('match_confidence', 0.0),
                        "age": analysis['age'],
                        "gender": analysis['gender'],
                        "gender_confidence": analysis['gender_confidence'],
                        "emotion": analysis['emotion'],
                        "emotion_confidence": analysis['emotion_confidence'],
                        "emotions_distribution": analysis['emotions_distribution']
                    })

                jpeg_b64 = camera.get_jpeg_base64(frame, quality=75)

                payload = {
                    "image": f"data:image/jpeg;base64,{jpeg_b64}",
                    "suspect_alert": suspect_detected,
                    "faces": analysis_results,
                    "is_real_camera": camera.is_real_camera,
                    "deepface_active": analyzer.deepface_available,
                    "timestamp": time.time()
                }

                await websocket.send_json(payload)

            elapsed = time.time() - t0
            await asyncio.sleep(max(0.01, interval - elapsed))

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket stream.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")

# Static Folders
public_dir = Path(__file__).parent.parent.parent / "public"
members_dir = public_dir / "members"

# Mount /members for avatar images
if members_dir.exists():
    app.mount("/members", StaticFiles(directory=str(members_dir)), name="members")

@app.get("/")
async def read_index():
    index_file = public_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(content={"message": "Face Recog API backend running. Public folder not found."})

# Mount static at root so paths like /style.css and /app.js work
if public_dir.exists():
    app.mount("/", StaticFiles(directory=str(public_dir)), name="static")
