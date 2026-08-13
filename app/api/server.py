import asyncio
import time
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.vision.camera_stream import CameraStream
from app.vision.face_detector import FaceDetector
from app.vision.analyzer import FaceAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FaceRecogAPI")

app = FastAPI(title="Face Analysis API - Age, Gender & Emotion Detection", version="1.0.0")

# Enable CORS for local web interfaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Vision Engine Instances
camera = CameraStream(camera_id=0, fps=30)
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
        "real_camera": camera.is_real_camera,
        "deepface_loaded": analyzer.deepface_available,
        "fps_target": camera.fps,
        "timestamp": time.time()
    }

@app.get("/api/snapshot")
async def get_snapshot():
    frame = camera.get_frame()
    if frame is None:
        return JSONResponse(status_code=500, content={"error": "No frame available"})

    faces = detector.detect_faces(frame)
    analysis_results = []

    for idx, f in enumerate(faces):
        face_id = f"face_{idx}"
        analysis = analyzer.analyze_crop(f['crop'], face_id=face_id)
        analysis_results.append({
            "box": {"x": f['x'], "y": f['y'], "w": f['w'], "h": f['h']},
            "confidence": f['confidence'],
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

                for idx, f in enumerate(faces):
                    face_id = f"face_{idx}"
                    analysis = analyzer.analyze_crop(f['crop'], face_id=face_id)
                    analysis_results.append({
                        "id": face_id,
                        "box": {"x": f['x'], "y": f['y'], "w": f['w'], "h": f['h']},
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

# Mount Static Files (Frontend UI)
public_dir = Path(__file__).parent.parent.parent / "public"
if public_dir.exists():
    app.mount("/static", StaticFiles(directory=str(public_dir)), name="static")

@app.get("/")
async def read_index():
    index_file = public_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(content={"message": "Face Recog API backend running. Public folder not found."})
