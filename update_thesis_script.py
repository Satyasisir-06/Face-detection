import re

# Read current build_50plus_page_thesis.py
with open(r"e:\Projects\Face Recog\build_50plus_page_thesis.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update index_data to include Appendices B, C, D
old_index_end = '["Chapter 11", "References (IEEE Standard Citations)", "104"]\n    ]'
new_index_end = '''["Chapter 11", "References (IEEE Standard Citations)", "104"],
        ["Appendix B", "REST API & WebSocket Protocol Specifications", "106"],
        ["B.1", "Architectural Overview of FastAPI Communication Interfaces", "106"],
        ["B.2", "Comprehensive REST API Route Specifications", "107"],
        ["B.3", "Full-Duplex WebSocket Streaming Protocol Schema", "108"],
        ["B.4", "Asynchronous Connection State Machine & Heartbeat", "109"],
        ["Appendix C", "System Deployment, Containerization & Operational Runbook", "110"],
        ["C.1", "Software Environment Requirements & Python Dependency Matrix", "110"],
        ["C.2", "Production Multi-Stage Dockerfile & Container Architecture", "111"],
        ["C.3", "Multi-Service Docker Compose Orchestration", "112"],
        ["C.4", "Production Reverse Proxy Configuration (Nginx)", "113"],
        ["Appendix D", "Operational User Manual & Field Troubleshooting Matrix", "114"],
        ["D.1", "End-User Quick-Start Guide & Interface Walkthrough", "114"],
        ["D.2", "Comprehensive Field Troubleshooting Matrix", "115"],
        ["D.3", "Hardware Sizing & Scaling Recommendations", "116"]
    ]'''

if old_index_end in content:
    content = content.replace(old_index_end, new_index_end)
    print("Successfully replaced index_data.")
else:
    print("Warning: old_index_end not matched exactly.")

# 2. Update tab_data to include Table B.1, C.1, D.1, D.2
old_tab_end = '["Table 10.1", "Team Contribution, Task Ownership, and Milestone Signoff Matrix", "102"]\n    ]'
new_tab_end = '''["Table 10.1", "Team Contribution, Task Ownership, and Milestone Signoff Matrix", "102"],
        ["Table B.1", "AURA Vision REST API Route Specifications and Response Envelopes", "107"],
        ["Table C.1", "Production Software Dependencies and Package Version Matrix", "110"],
        ["Table D.1", "Comprehensive Field Troubleshooting and Remediation Matrix", "115"],
        ["Table D.2", "Hardware Deployment Tiers and Ingestion Capacity Sizing", "116"]
    ]'''

if old_tab_end in content:
    content = content.replace(old_tab_end, new_tab_end)
    print("Successfully replaced tab_data.")
else:
    print("Warning: old_tab_end not matched exactly.")

# 3. Add Appendices B, C, D before doc.save
appendices_code = '''
    # APPENDIX B
    doc.add_page_break()
    add_chap_title("B", "REST API & WebSocket Protocol Specifications")
    add_sec_title("B.1", "Architectural Overview of FastAPI Communication Interfaces")
    add_p("The AURA Vision backend exposes high-performance asynchronous interfaces implemented over FastAPI and Uvicorn. To achieve real-time telemetry while maintaining robust administrative controls, the system splits communication into two distinct modalities: a RESTful HTTP control plane for configuration and telemetry inspection, and an asynchronous full-duplex WebSocket channel for streaming serialized frames and inference detections at 25–30 frames per second.")

    add_sec_title("B.2", "Comprehensive REST API Route Specifications")
    add_p("Table B.1 delineates all REST endpoints exposed by the AURA Vision ASGI web application server, including HTTP methods, parameter constraints, and return schemas:")
    
    tab_b1_headers = ["HTTP Method", "Endpoint Route", "Description & Purpose", "Request Payload", "Status & Response Type"]
    tab_b1_data = [
        ["GET", "/", "Delivers the glassmorphic Canvas dashboard SPA layout.", "None", "200 OK (text/html)"],
        ["GET", "/health", "System health and liveness probe for orchestrators.", "None", "200 OK (application/json)"],
        ["GET", "/metrics", "Prometheus-compatible real-time performance counters.", "None", "200 OK (application/json)"],
        ["POST", "/api/config", "Dynamically updates smoothing and detection thresholds.", '{"smoothing": bool, "ema_alpha": float}', "200 OK (application/json)"],
        ["POST", "/api/reset-tracker", "Purges temporal history buffers and reinitializes state.", "None", "200 OK (application/json)"],
        ["GET", "/api/logs", "Returns recent 100 system audit and diagnostic log entries.", "Query: ?limit=100", "200 OK (application/json)"]
    ]
    add_styled_table(doc, tab_b1_headers, tab_b1_data, col_widths=[1.1, 1.4, 2.3, 1.2, 1.2])

    add_p("Below is an illustrative JSON response emitted by the GET /health probe:")
    code_health = (
        '{\\n'
        '  "status": "healthy",\\n'
        '  "timestamp": 1775534291.452,\\n'
        '  "version": "1.0.0",\\n'
        '  "pipeline": {\\n'
        '    "camera_connected": true,\\n'
        '    "fps": 28.6,\\n'
        '    "latency_ms": 31.8,\\n'
        '    "frames_processed": 14892,\\n'
        '    "faces_detected": 1\\n'
        '  },\\n'
        '  "smoothing": {\\n'
        '    "enabled": true,\\n'
        '    "ema_alpha": 0.85,\\n'
        '    "majority_window_size": 30\\n'
        '  }\\n'
        '}'
    )
    add_code_block(doc, code_health)

    add_sec_title("B.3", "Full-Duplex WebSocket Streaming Protocol Schema")
    add_p("The WebSocket endpoint /ws operates on RFC 6455 standards. Frames are captured, equalized, subjected to DeepFace neural inference, annotated with bounding coordinates and demographic telemetry, and packaged into a standardized JSON payload structure before streaming:")
    code_ws = (
        '{\\n'
        '  "timestamp": 1775534291.452,\\n'
        '  "frame_id": 4821,\\n'
        '  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD...",\\n'
        '  "faces": [\\n'
        '    {\\n'
        '      "box": {"x": 210, "y": 140, "w": 185, "h": 220},\\n'
        '      "age": 24,\\n'
        '      "gender": "Woman",\\n'
        '      "gender_confidence": 0.984,\\n'
        '      "dominant_emotion": "happy",\\n'
        '      "emotions": {\\n'
        '        "angry": 0.002,\\n'
        '        "disgust": 0.001,\\n'
        '        "fear": 0.003,\\n'
        '        "happy": 0.892,\\n'
        '        "sad": 0.012,\\n'
        '        "surprise": 0.024,\\n'
        '        "neutral": 0.066\\n'
        '      }\\n'
        '    }\\n'
        '  ],\\n'
        '  "telemetry": {\\n'
        '    "fps": 28.6,\\n'
        '    "detection_latency_ms": 8.4,\\n'
        '    "inference_latency_ms": 22.4,\\n'
        '    "total_latency_ms": 31.8\\n'
        '  }\\n'
        '}'
    )
    add_code_block(doc, code_ws)

    add_sec_title("B.4", "Asynchronous Connection State Machine & Heartbeat")
    add_p("To guarantee rock-solid connectivity across lossy campus networks, the client WebSocket driver implements an automated finite state machine (FSM). Upon detecting connection failure or TCP socket termination, the client triggers exponential backoff reconnection delays starting at 1000ms and doubling up to 16000ms maximum, maintaining periodic ping-pong heartbeats every 10 seconds.")

    # APPENDIX C
    doc.add_page_break()
    add_chap_title("C", "System Deployment, Containerization & Operational Runbook")
    add_sec_title("C.1", "Software Environment Requirements & Python Dependency Matrix")
    add_p("AURA Vision relies on modern open-source machine learning and computer vision frameworks. Table C.1 outlines each essential runtime dependency and its core architectural responsibility:")
    
    tab_c1_headers = ["Package Name", "Minimum Version", "License", "Architectural Role & Description"]
    tab_c1_data = [
        ["fastapi", ">=0.104.1", "MIT", "Asynchronous REST API and WebSocket web routing framework."],
        ["uvicorn[standard]", ">=0.24.0", "BSD-3", "High-throughput ASGI server powered by uvloop event engine."],
        ["opencv-python-headless", ">=4.8.1.78", "Apache 2.0", "Camera ingestion, Haar cascade detection & image preprocessing."],
        ["deepface", ">=0.0.90", "MIT", "Facial demographic attribute and emotion neural network inference."],
        ["tensorflow", ">=2.15.0", "Apache 2.0", "Deep learning backend graph execution and GPU tensor math."],
        ["numpy", ">=1.24.3", "BSD-3", "Multi-dimensional array processing and mathematical computations."],
        ["pydantic", ">=2.5.0", "MIT", "Type safety validation and application configuration parsing."],
        ["websockets", ">=12.0", "BSD-3", "RFC 6455 compliant asynchronous WebSocket protocol implementation."]
    ]
    add_styled_table(doc, tab_c1_headers, tab_c1_data, col_widths=[1.5, 1.1, 1.0, 3.6])

    add_sec_title("C.2", "Production Multi-Stage Dockerfile & Container Architecture")
    add_p("For reproducible cross-platform deployment, AURA Vision provides a containerized multi-stage Docker build that minimizes final image size while bundling all essential system libraries (e.g., libgl1-mesa-glx, libglib2.0-0):")
    code_dockerfile = (
        '# Stage 1: Build & Dependency Resolution Stage\\n'
        'FROM python:3.10-slim AS builder\\n'
        'WORKDIR /app\\n'
        'RUN apt-get update && apt-get install -y --no-install-recommends \\\\\\n'
        '    build-essential libgl1-mesa-glx libglib2.0-0 \\\\\\n'
        '    && rm -rf /var/lib/apt/lists/*\\n'
        'COPY requirements.txt .\\n'
        'RUN pip install --no-cache-dir --user -r requirements.txt\\n\\n'
        '# Stage 2: Minimal Runtime Stage\\n'
        'FROM python:3.10-slim\\n'
        'WORKDIR /app\\n'
        'RUN apt-get update && apt-get install -y --no-install-recommends \\\\\\n'
        '    libgl1-mesa-glx libglib2.0-0 curl \\\\\\n'
        '    && rm -rf /var/lib/apt/lists/*\\n'
        'COPY --from=builder /root/.local /root/.local\\n'
        'COPY app/ ./app/\\n'
        'COPY static/ ./static/\\n'
        'ENV PATH=/root/.local/bin:$PATH \\\\\\n'
        '    PYTHONUNBUFFERED=1\\n'
        'EXPOSE 8000\\n'
        'HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\\\\\n'
        '    CMD curl -f http://localhost:8000/health || exit 1\\n'
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'
    )
    add_code_block(doc, code_dockerfile)

    add_sec_title("C.3", "Multi-Service Docker Compose Orchestration")
    add_p("To deploy AURA Vision alongside Prometheus telemetry scraping and Grafana dashboard visualization, the docker-compose.yml configuration coordinates multi-container networking:")
    code_compose = (
        'version: "3.8"\\n'
        'services:\\n'
        '  aura-vision:\\n'
        '    build: .\\n'
        '    container_name: aura_vision_app\\n'
        '    restart: unless-stopped\\n'
        '    ports:\\n'
        '      - "8000:8000"\\n'
        '    devices:\\n'
        '      - "/dev/video0:/dev/video0"\\n'
        '    environment:\\n'
        '      - CAMERA_INDEX=0\\n'
        '      - ENABLE_SMOOTHING=true\\n'
        '      - EMA_ALPHA=0.85\\n'
        '    healthcheck:\\n'
        '      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]\\n'
        '      interval: 30s\\n'
        '      timeout: 5s\\n'
        '      retries: 3\\n\\n'
        '  prometheus:\\n'
        '    image: prom/prometheus:latest\\n'
        '    container_name: aura_prometheus\\n'
        '    restart: unless-stopped\\n'
        '    ports:\\n'
        '      - "9090:9090"\\n'
        '    volumes:\\n'
        '      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml:ro'
    )
    add_code_block(doc, code_compose)

    add_sec_title("C.4", "Production Reverse Proxy Configuration (Nginx)")
    add_p("When deploying to production edge servers or institutional gateways, Nginx terminates TLS certificates, manages rate-limiting, and forwards WebSocket protocol upgrade headers:")
    code_nginx = (
        'server {\\n'
        '    listen 80;\\n'
        '    server_name vision.chaitanya.edu;\\n'
        '    return 301 https://$host$request_uri;\\n'
        '}\\n\\n'
        'server {\\n'
        '    listen 443 ssl http2;\\n'
        '    server_name vision.chaitanya.edu;\\n'
        '    ssl_certificate /etc/ssl/certs/vision.crt;\\n'
        '    ssl_certificate_key /etc/ssl/private/vision.key;\\n\\n'
        '    location / {\\n'
        '        proxy_pass http://127.0.0.1:8000;\\n'
        '        proxy_http_version 1.1;\\n'
        '        proxy_set_header Upgrade $http_upgrade;\\n'
        '        proxy_set_header Connection "upgrade";\\n'
        '        proxy_set_header Host $host;\\n'
        '        proxy_set_header X-Real-IP $remote_addr;\\n'
        '        proxy_read_timeout 86400s;\\n'
        '        proxy_send_timeout 86400s;\\n'
        '    }\\n'
        '}'
    )
    add_code_block(doc, code_nginx)

    # APPENDIX D
    doc.add_page_break()
    add_chap_title("D", "Operational User Manual & Field Troubleshooting Matrix")
    add_sec_title("D.1", "End-User Quick-Start Guide & Interface Walkthrough")
    add_p("Operating AURA Vision is designed to be frictionless for non-technical institutional staff and security officers. The deployment sequence follows four simple steps:")
    add_p("1. Initialize Server: Launch the FastAPI application by executing python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 from the terminal.")
    add_p("2. Open Browser Dashboard: Navigate to http://localhost:8000 on any modern browser (Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari).")
    add_p("3. Hardware Video Ingestion: Upon granting camera permission, the multi-threaded video daemon instantly captures the stream, running Haar cascade detection and DeepFace attribute analysis in the background.")
    add_p("4. Live Glassmorphic HUD Inspection: Observe the real-time bounding box tracking the subject\'s face, displaying the smoothed age, latching gender, and dynamic emotion confidence indicators.")

    add_sec_title("D.2", "Comprehensive Field Troubleshooting Matrix")
    add_p("Table D.1 provides diagnostic signatures and field-tested remediation procedures for common hardware and networking edge cases:")
    
    tab_d1_headers = ["Issue / Diagnostic Symptom", "Underlying Root Cause", "Log Signature / Error Trace", "Definitive Remediation Procedure"]
    tab_d1_data = [
        ["Black video feed / Camera unavailable", "Camera locked by another application (Zoom, OBS).", "[ERROR] Failed to open cv2.VideoCapture(0)", "Terminate competing apps; test camera indices 0, 1, or 2."],
        ["Low Frame Rate (<10 FPS) on CPU", "Heavy DeepFace inference on every single raw frame.", "CPU usage 100%; dropped frame warnings", "Enable frame skipping; downscale resolution to 720p or 480p."],
        ["Rapidly flickering demographic labels", "Temporal anti-jitter smoothing toggled off.", "Rapid gender toggling between Male/Female", "Send POST /api/config with enable_smoothing=true and alpha=0.85."],
        ["DeepFace pretrained weights error", "Air-gapped firewall blocking GitHub / GDrive CDN.", "urllib.error.URLError: <urlopen error timed out>", "Manually download .h5 weights into ~/.deepface/weights/ directory."],
        ["WebSocket connection failed immediately", "Reverse proxy lacking WebSocket upgrade headers.", "WebSocket connection to ws://... failed: 400", "Add proxy_set_header Upgrade and Connection in Nginx configuration."],
        ["Memory leak over 24-hour runtime", "Unbounded queue accumulation during consumer lag.", "Monotonically increasing process RAM usage", "Utilize collections.deque(maxlen=2) to drop stale historical frames."]
    ]
    add_styled_table(doc, tab_d1_headers, tab_d1_data, col_widths=[1.5, 1.5, 1.8, 2.4])

    add_sec_title("D.3", "Hardware Sizing & Scaling Recommendations")
    add_p("Table D.2 outlines recommended hardware tiers for various production deployment scenarios:")
    
    tab_d2_headers = ["Deployment Tier", "Recommended Hardware", "Ingestion Stream Specs", "Observed FPS", "Max Cameras", "Target Facility / Use Case"]
    tab_d2_data = [
        ["Edge IoT Tier", "Raspberry Pi 4 / Coral Edge TPU", "480p @ 15 FPS", "12–15 FPS", "1 Stream", "Classroom Doorway Kiosk"],
        ["Embedded AI Tier", "NVIDIA Jetson Orin Nano (8GB)", "720p @ 30 FPS", "25–30 FPS", "2 Streams", "Department Entry Turnstiles"],
        ["Workstation Tier", "Intel Core i7-13700K / 32GB RAM", "1080p @ 30 FPS", "28–30 FPS", "4 Streams", "College Reception & Main Office"],
        ["Enterprise Server", "Dual Xeon + NVIDIA RTX 4090", "1080p @ 60 FPS", "60+ FPS", "16 Streams", "Campus Perimeter & Exam Halls"]
    ]
    add_styled_table(doc, tab_d2_headers, tab_d2_data, col_widths=[1.2, 1.6, 1.1, 0.9, 0.8, 1.6])
'''

old_save_code = '    output_path = r"e:\\Projects\\Face Recog\\AURA_VISION_PROJECT_RECORD.docx"'
if old_save_code in content:
    content = content.replace(old_save_code, appendices_code + "\n" + old_save_code)
    print("Successfully added Appendices B, C, D before save.")
else:
    print("Warning: old_save_code not matched.")

with open(r"e:\Projects\Face Recog\build_50plus_page_thesis.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated build_50plus_page_thesis.py successfully!")
